#import <ApplicationServices/ApplicationServices.h>
#import <Foundation/Foundation.h>
#include <unistd.h>

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc < 3 || argc > 4) {
            fprintf(stderr, "usage: cgclick x y [clicks]\n");
            return 2;
        }
        CGPoint point = CGPointMake(atof(argv[1]), atof(argv[2]));
        int clicks = argc == 4 ? MAX(1, atoi(argv[3])) : 1;
        for (int click = 1; click <= clicks; click++) {
            CGEventRef down = CGEventCreateMouseEvent(NULL, kCGEventLeftMouseDown, point, kCGMouseButtonLeft);
            CGEventRef up = CGEventCreateMouseEvent(NULL, kCGEventLeftMouseUp, point, kCGMouseButtonLeft);
            CGEventSetIntegerValueField(down, kCGMouseEventClickState, click);
            CGEventSetIntegerValueField(up, kCGMouseEventClickState, click);
            CGEventPost(kCGHIDEventTap, down);
            usleep(60000);
            CGEventPost(kCGHIDEventTap, up);
            CFRelease(down);
            CFRelease(up);
            usleep(80000);
        }
    }
    return 0;
}
