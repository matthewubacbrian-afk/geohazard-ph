# Mobile Runtime Smoke Test

Use this checklist to verify the existing Nearby, Saved locations, and Alerts flows in
an installed debug app. Record results separately for each runtime. The [README mobile
section](../README.md#epic-4-mobile-nearby-alerts) has the project setup commands.

## Prepare a runtime and API

1. Start a development or staging API with `GET /api/v1/events` reachable from the
   runtime. Confirm the endpoint returns a JSON array. To exercise a nearby match,
   choose one event in that array and note its `latitude`, `longitude`, and
   `place_name`. If there are no events, mark the data-dependent checks blocked.
2. On Android, use JDK 17, Android Studio, SDK Platform 34, Build Tools 34.0.0,
   Platform Tools, and NDK 26.1.10909125. Run `npm ci` from `mobile/`, start Metro
   with `npm start`, then run `npm run android` in another terminal. An Android
   emulator reaches an API on the development computer through `10.0.2.2`; a
   physical phone needs a reachable LAN or HTTPS address.
3. On macOS, install Xcode and CocoaPods. Run `npm ci` from `mobile/`, `pod install`
   from `mobile/ios/`, start Metro with `npm start`, then run `npm run ios`. Use an
   API address reachable from the iOS simulator. Prefer HTTPS for a remote API;
   iOS App Transport Security can reject unsupported plain HTTP hosts.
4. Keep the reachable API base URL at hand for step 2 below. The value must end
   in `/api/v1`. Do not add a personal or secret URL to this document. Start
   from a fresh app install or clear the app's saved data before step 1.

## App flow

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Launch the app with no saved API URL or locations. | Nearby opens and prompts for an API URL and a saved location. The three tabs are reachable. |
| 2 | In Saved locations, enter an invalid API URL, then the reachable URL ending in `/api/v1`; tap Save API URL. | The invalid URL shows a validation error. The valid URL shows a saved message. |
| 3 | Try a blank location name, latitude outside -90 to 90, longitude outside -180 to 180, and radius outside 1 to 500 km. | Each invalid attempt is rejected and adds no location. |
| 4 | Save a named location using the selected event's exact coordinates and a 1 km radius. Tap Refresh events in Nearby. | The location appears in Saved locations. Nearby shows the selected event with place, source, time, magnitude when reported, and distance. Alerts shows the same match and states that background push is not configured. |
| 5 | Make the API unreachable after the event list has loaded; tap Refresh events. | Nearby and Alerts label the event data offline, keep the cached match visible, and offer Refresh events again. |
| 6 | Close and relaunch the app while the API remains unreachable. | The API URL, saved location, and cached event list remain available. The data is labeled offline after refresh fails. |
| 7 | Restore API access and refresh. Remove the matching location, then save a 1 km location whose coordinates are outside the radius of every event in the current feed. | The app clears the offline label after a successful refresh and displays “No events are within your saved radii.” |
| 8 | Remove the remaining test location. | Saved locations no longer lists it, and Nearby prompts for a saved location. |

If a valid event is unavailable, mark steps 4-7 blocked where they require a match or
cached event data. Do not count an empty feed as a successful proximity test. If a
platform cannot run, record the missing prerequisite instead of a pass.

## Record results

Fill one row after each actual run. Include the platform and OS version, app commit,
API environment name without credentials, completed steps, and a concise failure or
blocker. Link CI runs when recording build results.

| Date | Runtime and OS | App commit | API environment | Steps completed | Result and evidence |
| --- | --- | --- | --- | --- | --- |
|  | Android emulator or device |  |  |  |  |
|  | iOS simulator |  |  |  |  |

These foreground proximity matches are informational and are not official warnings
or forecasts. A simulator run does not verify background push, physical-device
behavior, production reliability, signing, or store distribution.
