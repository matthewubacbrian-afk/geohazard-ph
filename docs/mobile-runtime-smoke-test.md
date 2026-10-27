# Mobile Runtime Smoke Test

Use this checklist to verify the existing Nearby, Saved locations, and Alerts flows in
an installed debug app. Record results separately for each runtime. The [README mobile
section](../README.md#epic-4-mobile-nearby-alerts) has the project setup commands.

For the New Architecture readiness branch, build from its exact commit and record
Android and iOS results separately. A successful CI build verifies compilation,
not saved-location persistence, camera capture, SVG overlay rendering, or device
compatibility. Run the App flow below and the Scene review device checks on real
hardware before marking those flows verified.

## Epic 7 Scene Review (Android and iOS)

These device checks are pending until a camera-capable runtime and configured API are
available. Record Android and iOS independently; passing Jest does not verify native
permissions or camera behavior.

The native camera picker may place its capture in app-specific temporary cache storage;
`saveToPhotos` is disabled, and the feature clears its URI/base64 references on retake or
exit. The picker/OS manages removal of that temporary file; the feature does not copy it
to the photo library or retain a server-side image/history.

- [ ] Open **Scene review** and confirm no camera permission prompt appears until **Open camera** is tapped.
- [ ] Allow camera access, capture an indoor scene (for example, a kitchen or mall interior), and confirm the preview appears.
- [ ] Analyze the capture; verify candidate polygons align with the image, candidate selection updates the highlighted polygon, and the evidence checklist plus persistent visual-cue caveat are visible.
- [ ] Use a deliberately defocused capture; confirm the quality warning offers **Retake blurry photo** and **Continue anyway**, and that continuing sends the explicit override.
- [ ] Use a smooth or dim scene; record whether the provisional threshold warns on a usable image. Do not treat a passed synthetic test as calibration.
- [ ] Capture an outdoor scene and repeat the overlay/checklist check.
- [ ] Retake the photo and confirm the prior preview, candidate result, and selection are cleared before the camera reopens.
- [ ] Deny camera access and confirm an actionable permission message appears without crashing; grant access in system settings and retry.
- [ ] With API connectivity disabled, analyze a capture and confirm a safe retry message appears; restore connectivity and retry successfully.
- [ ] Confirm a no-candidate response has a clear empty state and still displays the caveat.
- [ ] Leave Scene review during and after analysis, return to it, and confirm the old image and analysis are gone.
- [ ] Verify no gallery permission or photo-library picker is requested; photos are sent only for the selected analysis and are not saved to history.

| Runtime | Camera/permission | API/overlay/checklist | Cleanup | Date / notes |
| --- | --- | --- | --- | --- |
| Android | Not run | Not run | Not run | Requires camera-capable device and configured API URL |
| iOS | Not run | Not run | Not run | Requires camera-capable device and configured API URL |

## Epic 7 Scene Review (Browser)

Run these checks in a camera-capable browser on `localhost` or HTTPS with the API model
provisioned. A browser test suite does not exercise actual permission prompts, camera
hardware, or API/model availability.

- [ ] Open `/scene-analysis` and confirm the page does not request camera permission before **Open camera** is selected.
- [ ] Allow permission, capture indoor and outdoor scenes, and confirm the preview aspect ratio is preserved and the camera track stops after capture.
- [ ] Analyze a capture and confirm the normalized polygon overlays the correct preview area; selection, absolute/relative area, compactness, model class confidence, ranking formula/value, evidence checklist, and caveat agree.
- [ ] Use a deliberately defocused capture; confirm the warning offers **Retake blurry photo** and **Continue anyway**, and that continuing sends `accept_quality_warning: true`.
- [ ] Use a smooth or dim scene and record any false warning; the threshold is provisional and requires held-out benchmark calibration.
- [ ] Retake and leave the page during pending capture/analysis; confirm old preview/results are cleared, tracks stop, and pending requests are aborted.
- [ ] Deny camera permission or use an unsupported/insecure context; confirm an actionable state appears without a crash.
- [ ] Make the API unavailable, retry after restoring it, and confirm a safe error/retry state and no image data in logs or history.
- [ ] Confirm a no-candidate response still shows its limitation caveat.

| Runtime | Camera/permission | API/overlay/checklist | Cleanup | Date / notes |
| --- | --- | --- | --- | --- |
| Browser | Not run | Not run | Not run | Requires camera-capable browser and model-provisioned API; current default API image returns typed unavailable response |

## Prepare a runtime and API

1. Start a development or staging API with `GET /api/v1/events` and
   `POST /api/v1/scene-analyses` reachable from the runtime. Confirm the events endpoint returns a JSON array. To exercise a nearby match,
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
| 1 | Launch the app with no saved API URL or locations. | Nearby opens and prompts for an API URL and a saved location. All four tabs are reachable. |
| 2 | In Saved locations, enter an invalid API URL, then the reachable URL ending in `/api/v1`; tap Save API URL. | The invalid URL shows a validation error. The valid URL shows a saved message. |
| 3 | Try a blank location name, latitude outside -90 to 90, longitude outside -180 to 180, and radius outside 1 to 500 km. | Each invalid attempt is rejected and adds no location. |
| 4 | Save a named location using the selected event's exact coordinates and a 1 km radius. Tap Refresh events in Nearby. | The location appears in Saved locations. Nearby shows the selected event with place, source, time, magnitude when reported, and distance. Alerts shows the same match and states that background push is not configured. |
| 5 | Make the API unreachable after the event list has loaded; tap Refresh events. | Nearby and Alerts label the event data offline, keep the cached match visible, and offer Refresh events again. |
| 6 | Close and relaunch the app while the API remains unreachable. | The API URL, saved location, and cached event list remain available. The data is labeled offline after refresh fails. |
| 7 | Restore API access and refresh. Remove the matching location, then save a 1 km location whose coordinates are outside the radius of every event in the current feed. | The app clears the offline label after a successful refresh and displays “No events are within your saved radii.” |
| 8 | Remove the remaining test location. | Saved locations no longer lists it, and Nearby prompts for a saved location. |
| 9 | Open Scene review, capture a photo, and run scene analysis. | Candidate areas, visible cues, and limitations appear under the persistent visual-cue caveat; no image history is created. |

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
