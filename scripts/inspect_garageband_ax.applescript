on safeAttribute(theElement, attributeName)
    tell application "System Events"
        try
            return value of attribute attributeName of theElement as text
        on error
            return ""
        end try
    end tell
end safeAttribute

tell application "System Events"
    tell application process "GarageBand"
        set outputLines to {}
        repeat with windowIndex from 1 to count of windows
            set currentWindow to window windowIndex
            set end of outputLines to "WINDOW " & windowIndex & " | " & my safeAttribute(currentWindow, "AXTitle")
            try
                set orderedChildren to value of attribute "AXChildrenInNavigationOrder" of currentWindow
                repeat with childElement in orderedChildren
                    set childRole to my safeAttribute(childElement, "AXRole")
                    set childDescription to my safeAttribute(childElement, "AXDescription")
                    set childTitle to my safeAttribute(childElement, "AXTitle")
                    set childValue to my safeAttribute(childElement, "AXValue")
                    set end of outputLines to childRole & " | " & childDescription & " | " & childTitle & " | " & childValue
                end repeat
            end try
        end repeat
    end tell
end tell

set AppleScript's text item delimiters to linefeed
set outputText to outputLines as text
set AppleScript's text item delimiters to ""
return outputText
