---
title: "Estimate Input Tokens - MiniMax API Docs"
url: "https://platform.minimax.io/docs/api-reference/responses-input-tokens"
requestedUrl: "https://platform.minimax.io/docs/api-reference/responses-input-tokens"
coverImage: "https://filecdn.minimax.chat/public/58eca777-e31f-448a-9823-e2220e49b426.png"
siteName: "MiniMax API Docs"
summary: "Estimate the input token count of a request without invoking the model. Useful for evaluating request cost or checking context length limits before calling the main endpoint."
adapter: "generic"
capturedAt: "2026-08-02T07:47:52.821Z"
conversionMethod: "defuddle"
kind: "generic/article"
language: "en"
---

Estimate Input Tokens

```
curl --request POST \
  --url https://api.minimax.io/v1/responses/input_tokens \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "model": "MiniMax-M3",
  "input": [
    {
      "type": "message",
      "role": "user",
      "content": "Please implement a generic quicksort algorithm in Python with these requirements: 1) in-place sorting to save memory; 2) three-way partitioning to handle duplicate elements; 3) switch to insertion sort for small subarrays; 4) include complete unit tests. Finally, explain the advantage of three-way partitioning over the classic Lomuto scheme when keys repeat."
    }
  ],
  "tools": [
    {
      "type": "function",
      "name": "search_docs",
      "description": "Search the official documentation of the Python standard library or a third-party package",
      "parameters": {
        "type": "object",
        "properties": {
          "library": {
            "type": "string",
            "description": "Library name, e.g. \`typing\`, \`itertools\`"
          },
          "query": {
            "type": "string",
            "description": "Search keywords"
          }
        },
        "required": [
          "library",
          "query"
        ]
      }
    },
    {
      "type": "function",
      "name": "run_python",
      "description": "Execute Python code in a sandbox and return stdout / error",
      "parameters": {
        "type": "object",
        "properties": {
          "code": {
            "type": "string",
            "description": "Python code to execute"
          },
          "timeout_seconds": {
            "type": "integer",
            "description": "Execution timeout in seconds",
            "default": 10
          }
        },
        "required": [
          "code"
        ]
      }
    }
  ]
}
'
```

```
{
  "object": "response.input_tokens",
  "input_tokens": 588
}
```

POST

/

v1

/

responses

/

input\_tokens

Estimate Input Tokens

```
curl --request POST \
  --url https://api.minimax.io/v1/responses/input_tokens \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "model": "MiniMax-M3",
  "input": [
    {
      "type": "message",
      "role": "user",
      "content": "Please implement a generic quicksort algorithm in Python with these requirements: 1) in-place sorting to save memory; 2) three-way partitioning to handle duplicate elements; 3) switch to insertion sort for small subarrays; 4) include complete unit tests. Finally, explain the advantage of three-way partitioning over the classic Lomuto scheme when keys repeat."
    }
  ],
  "tools": [
    {
      "type": "function",
      "name": "search_docs",
      "description": "Search the official documentation of the Python standard library or a third-party package",
      "parameters": {
        "type": "object",
        "properties": {
          "library": {
            "type": "string",
            "description": "Library name, e.g. \`typing\`, \`itertools\`"
          },
          "query": {
            "type": "string",
            "description": "Search keywords"
          }
        },
        "required": [
          "library",
          "query"
        ]
      }
    },
    {
      "type": "function",
      "name": "run_python",
      "description": "Execute Python code in a sandbox and return stdout / error",
      "parameters": {
        "type": "object",
        "properties": {
          "code": {
            "type": "string",
            "description": "Python code to execute"
          },
          "timeout_seconds": {
            "type": "integer",
            "description": "Execution timeout in seconds",
            "default": 10
          }
        },
        "required": [
          "code"
        ]
      }
    }
  ]
}
'
```

```
{
  "object": "response.input_tokens",
  "input_tokens": 588
}
```

#### Authorizations

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#authorization-authorization)

Authorization

string

header

required

`HTTP: Bearer Auth`

- Security Scheme Type: http
- HTTP Authorization Scheme: Bearer API\_key, used to authenticate your account. View it in [Account Management > API Keys](https://platform.minimax.io/user-center/basic-information/interface-key)

#### Headers

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#parameter-content-type)

Content-Type

enum<string>

default:application/json

required

Media type of the request body. Must be set to `application/json`

Available options:

`application/json`

#### Body

application/json

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#body-model)

model

string

required

Model name to invoke, e.g. `MiniMax-M3`

Example:

`"MiniMax-M3"`

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#body-input-one-of-0)

input

required

Conversation content. Supports either a simple text or a full conversation history array

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#body-instructions)

instructions

string

System instructions

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#body-tools)

tools

object\[\]

Tool list

Show child attributes

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#body-tool-choice)

tool\_choice

enum<string>

Tool selection strategy: `none` means no tool will be called; `auto` lets the model decide whether to call tools

Available options:

`none`,

`auto`

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#body-text)

text

object

Output format control

Show child attributes

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#body-reasoning)

reasoning

object

Reasoning control. For MiniMax-M3, the default is `none`, which disables reasoning. Set `effort` to a non-`none` value (`minimal`, `low`, `medium`, or `high`) to enable Adaptive Thinking, but this does not tune MiniMax-M3's reasoning depth. For M2.x models, reasoning cannot be disabled.

Show child attributes

#### Response

200 - application/json

Successful response

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#response-object)

object

enum<string>

required

Object type, always `response.input_tokens`

Available options:

`response.input_tokens`

[​

](https://platform.minimax.io/docs/api-reference/responses-input-tokens#response-input-tokens)

input\_tokens

integer

required

Estimated input token count

[Create Response](https://platform.minimax.io/docs/api-reference/responses-create)[Create Video Generation Task](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)