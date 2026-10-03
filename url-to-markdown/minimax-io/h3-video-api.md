---
title: "Create Video Generation Task - MiniMax API Docs"
url: "https://platform.minimax.io/docs/api-reference/video-generation-v2-create"
requestedUrl: "https://platform.minimax.io/docs/api-reference/video-generation-v2-create"
coverImage: "https://filecdn.minimax.chat/public/58eca777-e31f-448a-9823-e2220e49b426.png"
siteName: "MiniMax API Docs"
summary: "Video generation V2 endpoint. Provide multimodal input via the content array (text / image / video / audio) to support text-to-video, image-to-video (first & last frame), and reference-to-video, with 2K output."
adapter: "generic"
capturedAt: "2026-08-02T07:47:06.728Z"
conversionMethod: "defuddle"
kind: "generic/article"
language: "en"
---

# Create Video Generation Task - MiniMax API Docs

POST

/

v2

/

video\_generation

#### AuthorizationsAuthorization

string

header

required

`HTTP: Bearer Auth`

- Security Scheme Type: http
- HTTP Authorization Scheme: `Bearer API_key`, used to verify account information, can be found in [Account Management>API Keys](https://platform.minimax.io/user-center/basic-information/interface-key).

#### HeadersContent-Type

enum<string>

default:application/json

required

Media type of the request body. Set it to `application/json`.

Available options:

`application/json`

#### Body

application/jsonmodel

enum<string>

required

Model name. Currently available: `MiniMax-H3`.

Available options:

`MiniMax-H3`content

object\[\]

required

Array of multimodal input describing the information used to generate the video. Each element is distinguished by `type` (`text` / `image_url` / `video_url` / `audio_url`) and can be labeled with a `role`.

Every request must include one non-empty `text` item (the prompt is required); otherwise a parameter error is returned.

Supported input combinations (corresponding to different generation scenarios):

- Text-to-video: a single `text` element only.
- Image-to-video, first frame: `text` + 1 `image_url` (`role=first_frame`, or omitted).
- Image-to-video, last frame: `text` + 1 `image_url` (`role=last_frame`).
- Image-to-video, first & last frame: `text` + 2 `image_url` items with `role` set to `first_frame` and `last_frame` respectively.
- Reference-to-video: `text` + any combination of reference images (`role=reference_image`), reference videos (`role=reference_video`), and reference audio (`role=reference_audio`); audio alone is not allowed, at least one reference video or image is required.

> Image-to-video and reference-to-video are mutually exclusive: if any `reference_image` / `reference_video` / `reference_audio` role appears in content, then `first_frame` / `last_frame` must not appear (and vice versa); the two cannot be mixed.

---

Input media limits (total request body ≤ 64 MB; use public URLs for large files, avoid Base64)

Image `image_url`:

| Item | Limit |
| --- | --- |
| Format | JPG, JPEG, PNG, WEBP, HEIC, HEIF |
| Single file size | ≤ 30 MB |
| Width/height range | \[256, 5760\] px |
| Aspect ratio (w/h) | \[0.4, 2.5\] |
| Count | first frame ≤ 1, last frame ≤ 1, reference images ≤ 9 |

Video `video_url` (reference scenario only):

| Item | Limit |
| --- | --- |
| Container / format | MP4 (`.mp4`), MOV (`.mov`) |
| Codec | Video H.264/AVC, H.265/HEVC; audio AAC, MP3 |
| Single file size | ≤ 50 MB |
| Count | ≤ 3 |
| Per-clip duration | \[2, 15\] s; total ≤ 15 s |
| Width/height range | \[256, 5760\] px |
| Aspect ratio (w/h) | \[0.4, 2.5\] |
| Frame rate | \[23.976, 60\] |

Audio `audio_url` (reference scenario only):

| Item | Limit |
| --- | --- |
| Format | WAV, MP3 |
| Single file size | ≤ 15 MB |
| Count | ≤ 3 |
| Per-clip duration | \[2, 15\] s; total ≤ 15 s |resolution

enum<string>

required

Video resolution. Currently available: `768P`, `2K`.

Available options:

`768P`,

`2K`duration

enum<integer>

required

Duration of the generated video in seconds. Required, integer. Available values: `4` - `15`.

Available options:

`4`,

`5`,

`6`,

`7`,

`8`,

`9`,

`10`,

`11`,

`12`,

`13`,

`14`,

`15`ratio

enum<string>

Aspect ratio of the generated video. Defaults to `adaptive` (the most suitable ratio is chosen automatically based on the input; the actual ratio can be read from the `ratio` field of the query endpoint). Available values: `adaptive`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`.

Text-to-video (t2va, content contains only `text`): `ratio` is required and cannot be `adaptive`; available values `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`.

Image-to-video (i2va, content contains a `first_frame` / `last_frame` image): the aspect ratio is determined by the input image and `ratio` is always `adaptive`; passing another valid value does not error but is ignored and treated as `adaptive`.

Reference-to-video (r2va, content contains `reference_image` / `reference_video` / `reference_audio`): `ratio` is optional and defaults to `adaptive`; you may also explicitly specify any of the concrete ratios above.

Available options:

`adaptive`,

`21:9`,

`16:9`,

`4:3`,

`1:1`,

`3:4`,

`9:16`callback\_url

string

Callback URL for task status changes. Once configured, the MiniMax server first sends a verification request containing a `challenge` field (you must return the `challenge` unchanged within 3 seconds to complete verification); after verification succeeds, it POSTs an update to this URL whenever the task status changes. The push body has the same structure as the response of the [Query video generation task](https://platform.minimax.io/docs/api-reference/video-generation-v2-query) endpoint.

Callback `status` values: `queued`, `running`, `succeeded`, `failed`, `expired`.

#### Responsetask\_id

string

ID of the video generation task, used to query the task status later.

[Estimate Input Tokens](https://platform.minimax.io/docs/api-reference/responses-input-tokens) [Query Video Generation Task](https://platform.minimax.io/docs/api-reference/video-generation-v2-query)