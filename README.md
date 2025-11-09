# paperless-ai-processing-service

Post process your [paperless-ngx](https://docs.paperless-ngx.com/) documents with your private and local LLMs after ingesting or updating.

This project is based on the project [ngx-renamer](https://github.com/chriskoch/ngx-renamer). But I was not happy with the limitation that paperless-ngx post-consumption cant be triggered without completely re-adding a document to the platform. With this service the documents ai-processing gets triggered by the webhook feature on every document update or addition or even when scheduled.

For the time being the service supports the connection to a [Open WebUI](https://docs.openwebui.com/) instance via openai-compatible api. This way its possible to use local ai (i.e. ollama) or any other AI service as long as it is connected through your chosen Open WebUI instance.

Further improvements and robustness will follow soon. Use it at your own risk.

Currently working features:

- generation of title based on file content
- local LLM via Open WebUI
- paperless-ngx webhook support

## Getting started

### Create paperless-ngx api token

- optional: create a new user for automation work
- create api token via https://your-paperless-url/admin/authtoken/tokenproxy/
- add api token to container env-variables `PAPERLESS_NGX_API_KEY`

### Create Open WebUI api token

- create api token for your open web ui service according to the [documentation](https://docs.openwebui.com/getting-started/api-endpoints/#authentication)
- add api token to container env-variables `OPENAI_API_KEY`

### run the container along side your paperless-ngx stack

```bash
  # ... your paperless-ngx compose stack

  webhook_service:
    image: paperless-ai-processing-service:1.0
    container_name: paperless-ai-processing-service

    # optional, only when you want to modify the llm prompts
    # volumes:
    #   - /volume1/docker/paperlessngx/paperless-ai-processing-service:/usr/src/app

    restart: unless-stopped
    environment:
      # your paperless api route within the docker stack
      - PAPERLESS_NGX_URL=http://PaperlessNGX:8000/api
      # your paperless api key
      - PAPERLESS_NGX_API_KEY="SET ME"
      # your Open WebUI url
      - OPENAI_BASE_URL=https://your-open-web-ui/api
      # your Open WebUI api key
      - OPENAI_API_KEY="SET ME"
```

### Optional: Download or checkout the source code

**(only when you want to modify the llm prompts)**

You may edit `settings.yaml` to edit the prompt and with that the results.

- Copy the directory into your paperless docker compose directory (where the `docker-compose.yml` is located).

```bash
# It will look like this
.
└── paperless-ai-processing-service
    ...
    ├── settings.yaml
    ...
```

Now you can adjust the llm model and model-name to your likening. More on this in the future.

### Set up [webhook](https://docs.paperless-ngx.com/usage/) in paperless-ngx

**Important**: to avoid endless loops you need to carefully follow the steps of adding triggers and assignment of tags.

- create a new tag named `ai-processed`
- create a new webhook named "Generate AI Title" or similar
- add triggers:
  - for "Document updated" and set advanced filter
    "Does not have these tags: `ai-processed`"
  - for "Document added" and set advanced filter
    "Does not have these tags: `ai-processed`"
- add action:
  - Assignment: assign tag `ai-processed`,
    this will avoid endless update loops
  - Webhook:
    - Webhook url: `http://paperless-ai-processing-service:5000/document/changed`
      this is your url to the service container so the URL should be correct if hosted in the same docker stack.
    - Use parameters for webhook body: `true`
    - Send webhook payload as JSON: `true`
    - Webhook Params: `url`:`{{doc_url}}`
- press save

## The settings

**Test the different models at OpenAI:**

```yaml
openai_model: "gpt-4o-mini" # the model to use for the generation
```

**Decide whether you want to have a date as a prefix:**

```yaml
with_date: true # boolean if the title should the date as a prefix
```

**Play with the prompt - it is a work in progress and tested in Englsh and German:**

```yaml
prompt:
  # the main prompt for the AI
  main: |
    - Begin the text with: BEGIN: """
    - End the text with: """ END: <title>GENERATED_TITLE</title>
    - Generate a concise, informative title in the corresponding language
    - Include the sender or author (max 20 characters) in the title
    - Remove all stop words from the title
    - Ensure the title is unique and free of duplicate information
    - Keep the title under 127 characters
    - Avoid using asterisks in the title
    - Optimize the title for readability
    - Check the title against filename conventions
    - Re-read and further optimize the title if necessary
  # the prompt part will be appended if the date should be included in the title using with_date: true
  with_date: |
    * analyze the text and find the date of the document
    * add the found date in form YYYY-MM-DD as a prefix to the doument title
    * if there is no date information in the document, use {current_date}
    * use the form: date sender title
  # the prompt part will be appended if the date should not be included in the title using with_date: false
  no_date: |
    * use the form: sender title
  # the prompt before the content of the document will be appended
  pre_content: |
    ### begin of text ###
  # the prompt after the content of the document will be appended
  post_content: |
    ### end of text ###
```
