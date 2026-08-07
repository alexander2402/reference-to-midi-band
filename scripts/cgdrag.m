#import <ApplicationServices/ApplicationServices.h>
#import <Foundation/Foundation.h>
#include <unistd.h>

static void postMouse(CGEventType type, CGPoint point) {
    CGEventRef event = CGEventCreateMouseEvent(NULL, type, point, kCGMouseButtonLeft);
    CGEventPost(kCGHIDEventTap, event);
    CFRelease(event);
}

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc != 5) {
            fprintf(stderr, "usage: cgdrag start_x start_y end_x end_y\n");
            return 2;
        }
        CGPoint start = CGPointMake(atof(argv[1]), atof(argv[2]));
        CGPoint finish = CGPointMake(atof(argv[3]), atof(argv[4]));
        postMouse(kCGEventMouseMoved, start);
        usleep(80000);
        postMouse(kCGEventLeftMouseDown, start);
        for (int step = 1; step <= 12; step++) {
            double fraction = (double)step / 12.0;
            CGPoint point = CGPointMake(
                start.x + (finish.x - start.x) * fraction,
                start.y + (finish.y - start.y) * fraction
            );
            postMouse(kCGEventLeftMouseDragged, point);
            usleep(30000);
        }
        postMouse(kCGEventLeftMouseUp, finish);
    }
    return 0;
}
