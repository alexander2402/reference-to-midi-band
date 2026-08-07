#import <AVFoundation/AVFoundation.h>
#import <AudioToolbox/AudioToolbox.h>
#import <Foundation/Foundation.h>

static void Fail(NSString *message, NSError *error) {
    if (error) {
        fprintf(stderr, "%s: %s\n", message.UTF8String, error.localizedDescription.UTF8String);
    } else {
        fprintf(stderr, "%s\n", message.UTF8String);
    }
    exit(1);
}

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc != 3 && argc != 4) {
            fprintf(stderr, "Usage: render_midi INPUT.mid OUTPUT.wav [program_override]\n");
            return 1;
        }

        NSURL *inputURL = [NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[1]]];
        NSURL *outputURL = [NSURL fileURLWithPath:[NSString stringWithUTF8String:argv[2]]];
        NSURL *soundBankURL = [NSURL fileURLWithPath:
            @"/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls"];

        AVAudioEngine *engine = [[AVAudioEngine alloc] init];
        AVAudioSequencer *sequencer = [[AVAudioSequencer alloc] initWithAudioEngine:engine];
        NSError *error = nil;
        if (![sequencer loadFromURL:inputURL
                            options:0
                              error:&error]) {
            Fail(@"Could not load MIDI", error);
        }

        NSArray<AVMusicTrack *> *tracks = sequencer.tracks;
        const UInt8 programsFive[] = {90, 33, 0, 52, 98};
        const UInt8 programsSix[] = {0, 90, 33, 0, 52, 98};
        UInt8 programsSeparate[] = {0, 0};
        UInt8 programsOverride[128] = {0};
        const UInt8 *programs = NULL;
        NSInteger drumIndex = -1;
        if (tracks.count == 5) {
            programs = programsFive;
            drumIndex = 2;
        } else if (tracks.count == 6) {
            programs = programsSix;
            drumIndex = 3;
        } else if (tracks.count == 2) {
            NSString *filename = inputURL.lastPathComponent;
            if ([filename hasPrefix:@"01_"]) programsSeparate[1] = 90;
            else if ([filename hasPrefix:@"02_"]) programsSeparate[1] = 33;
            else if ([filename hasPrefix:@"03_"]) {
                programsSeparate[1] = 0;
                drumIndex = 1;
            }
            else if ([filename hasPrefix:@"04_"]) programsSeparate[1] = 52;
            else if ([filename hasPrefix:@"05_"]) programsSeparate[1] = 98;
            else Fail(@"Could not infer the instrument for separate MIDI", nil);
            if (argc == 4) {
                NSInteger override = [[NSString stringWithUTF8String:argv[3]] integerValue];
                if (override < 0 || override > 127) Fail(@"Program override must be 0-127", nil);
                programsSeparate[1] = (UInt8)override;
            }
            programs = programsSeparate;
        } else {
            Fail([NSString stringWithFormat:@"Expected two, five, or six tracks, found %lu",
                  (unsigned long)tracks.count], nil);
        }

        if (argc == 4 && tracks.count != 2) {
            NSString *value = [NSString stringWithUTF8String:argv[3]];
            NSArray<NSString *> *parts = [value componentsSeparatedByString:@","];
            if (parts.count != tracks.count) {
                Fail(@"Full-arrangement override must provide one comma-separated program per track", nil);
            }
            for (NSUInteger index = 0; index < parts.count; index++) {
                NSInteger override = parts[index].integerValue;
                if (override < 0 || override > 127) Fail(@"Program override must be 0-127", nil);
                programsOverride[index] = (UInt8)override;
            }
            programs = programsOverride;
        }

        NSMutableArray<AVAudioUnitSampler *> *samplers = [NSMutableArray array];
        for (NSUInteger index = 0; index < tracks.count; index++) {
            AVAudioUnitSampler *sampler = [[AVAudioUnitSampler alloc] init];
            [samplers addObject:sampler];
            [engine attachNode:sampler];
            [engine connect:sampler to:engine.mainMixerNode format:nil];
            UInt8 bankMSB = index == drumIndex
                ? kAUSampler_DefaultPercussionBankMSB
                : kAUSampler_DefaultMelodicBankMSB;
            error = nil;
            if (![sampler loadSoundBankInstrumentAtURL:soundBankURL
                                               program:programs[index]
                                               bankMSB:bankMSB
                                               bankLSB:kAUSampler_DefaultBankLSB
                                                 error:&error]) {
                Fail(@"Could not load DLS instrument", error);
            }
            tracks[index].destinationAudioUnit = sampler;
        }

        AVAudioFormat *format = [[AVAudioFormat alloc] initStandardFormatWithSampleRate:44100
                                                                              channels:2];
        const AVAudioFrameCount maximumFrames = 4096;
        error = nil;
        if (![engine enableManualRenderingMode:AVAudioEngineManualRenderingModeOffline
                                        format:format
                             maximumFrameCount:maximumFrames
                                         error:&error]) {
            Fail(@"Could not enable offline rendering", error);
        }

        AVAudioFile *outputFile = [[AVAudioFile alloc] initForWriting:outputURL
                                                              settings:format.settings
                                                                 error:&error];
        if (!outputFile) {
            Fail(@"Could not create output file", error);
        }
        AVAudioPCMBuffer *buffer = [[AVAudioPCMBuffer alloc]
            initWithPCMFormat:engine.manualRenderingFormat
                frameCapacity:maximumFrames];
        if (!buffer) {
            Fail(@"Could not create render buffer", nil);
        }

        [engine prepare];
        error = nil;
        if (![engine startAndReturnError:&error]) {
            Fail(@"Could not start audio engine", error);
        }
        sequencer.currentPositionInBeats = 0;
        error = nil;
        if (![sequencer startAndReturnError:&error]) {
            Fail(@"Could not start sequencer", error);
        }

        AVMusicTimeStamp lengthInBeats = 0;
        for (AVMusicTrack *track in tracks) {
            lengthInBeats = MAX(lengthInBeats, track.lengthInBeats);
        }
        NSTimeInterval musicalSeconds = [sequencer secondsForBeats:lengthInBeats];
        NSTimeInterval totalSeconds = musicalSeconds + 4.0;
        AVAudioFramePosition totalFrames = (AVAudioFramePosition)(totalSeconds * format.sampleRate);

        while (engine.manualRenderingSampleTime < totalFrames) {
            AVAudioFramePosition remaining = totalFrames - engine.manualRenderingSampleTime;
            AVAudioFrameCount frames = (AVAudioFrameCount)MIN((AVAudioFramePosition)maximumFrames, remaining);
            error = nil;
            AVAudioEngineManualRenderingStatus status = [engine renderOffline:frames
                                                                      toBuffer:buffer
                                                                         error:&error];
            if (status == AVAudioEngineManualRenderingStatusSuccess) {
                if (![outputFile writeFromBuffer:buffer error:&error]) {
                    Fail(@"Could not write render buffer", error);
                }
            } else if (status == AVAudioEngineManualRenderingStatusCannotDoInCurrentContext) {
                continue;
            } else if (status == AVAudioEngineManualRenderingStatusInsufficientDataFromInputNode) {
                continue;
            } else {
                Fail(@"Offline render returned an error", error);
            }
        }

        [sequencer stop];
        [engine stop];
        printf("Rendered %lu tracks, %.3f seconds\n", (unsigned long)tracks.count, totalSeconds);
    }
    return 0;
}
