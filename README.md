# paperless-ai-processing-service

Post-process your [paperless-ngx](https://docs.paperless-ngx.com/) documents with your private and local LLMs after ingesting or updating.

This project is based on the project [ngx-renamer](https://github.com/chriskoch/ngx-renamer). However, I was not happy with the limitation that paperless-ngx post-consumption can't be triggered without completely re-adding a document to the platform. With this service, the document's AI processing is triggered by the webhook feature on every document update, addition, or even when scheduled.

For the time being, the service supports the connection to an [Open WebUI](https://docs.openwebui.com/) instance via an OpenAI-compatible API. This way, it's possible to use local AI (e.g., Ollama) or any other AI service as long as it is connected through your chosen Open WebUI instance.

Further improvements and robustness will follow soon. Use it at your own risk.

Currently working features:

- Generation of titles based on file content
- Local LLM via Open WebUI
- Paperless-ngx webhook support

## Getting started

### Create paperless-ngx API token

- Optional: create a new user for automation work
- Create an API token via https://your-paperless-url/admin/authtoken/tokenproxy/
- Add the API token to container environment variables `PAPERLESS_NGX_API_KEY`

### Create Open WebUI API token

- Create an API token for your Open WebUI service according to the [documentation](https://docs.openwebui.com/getting-started/api-endpoints/#authentication)
- Add the API token to container environment variables `OPENAI_API_KEY`

### Run the container alongside your paperless-ngx stack

```bash
  # ... your paperless-ngx compose stack

  webhook_service:
    image: beyeja/paperless-ai-processing-service:1.0
    container_name: paperless-ai-processing-service

    # Optional, only when you want to modify the LLM prompts
    # volumes:
    #   - ./settings.yaml:/usr/src/app/settings.yaml

    restart: unless-stopped
    environment:
      # Your paperless API route within the docker stack
      - PAPERLESS_NGX_URL=http://PaperlessNGX:8000/api
      # Your paperless API key
      - PAPERLESS_NGX_API_KEY="SET ME"
      # Your Open WebUI URL
      - OPENAI_BASE_URL=https://your-open-web-ui/api
      # Your Open WebUI API key
      - OPENAI_API_KEY="SET ME"
      # optional tag id that is added to indicate updated document
      - PAPERLESS_NGX_UPDATED_TAG_ID=5
```

### Optional: Download or check out the source code

**(Only when you want to modify the LLM prompts)**

You may edit `settings.yaml` to adjust the prompt and, with that, the results.

- Copy the directory into your paperless docker-compose directory (where the `docker-compose.yml` is located).

```bash
# It will look like this
.
└── paperless-ai-processing-service
    ...
    ├── settings.yaml
    ...
```

Now you can adjust the LLM model and model name to your liking. More on this in the future.

### Set up [webhook](https://docs.paperless-ngx.com/usage/) in paperless-ngx

**Important**: To avoid endless loops, you need to carefully follow the steps of adding triggers and assigning tags.

- Create a new tag named `ai-processed`
- Create a new webhook named "Generate AI Title" or similar
- Add triggers:
  - For "Document updated" and set advanced filter:
    "Does not have these tags: `ai-processed`"
  - For "Document added" and set advanced filter:
    "Does not have these tags: `ai-processed`"
- Add action:
  - Assignment: assign tag `ai-processed`,
    this will avoid endless update loops
  - Webhook:
    - Webhook URL: `http://paperless-ai-processing-service:5000/document/changed`
      This is your URL to the service container, so the URL should be correct if hosted in the same docker stack.
    - Use parameters for webhook body: `true`
    - Send webhook payload as JSON: `true`
    - Webhook Params: `url`:`{{doc_url}}`
- Press save

## The settings

**Test the different models at OpenAI:**

```yaml
openai_model: "gpt-4o-mini" # The model to use for the generation
```

**Decide whether you want to have a date as a prefix:**

```yaml
with_date: true # Boolean if the title should include the date as a prefix
```

**Play with the prompt - it is a work in progress and tested in English and German:**

```yaml
prompt:
  # The main prompt for the AI
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
  # The prompt part will be appended if the date should be included in the title using with_date: true
  with_date: |
    * Analyze the text and find the date of the document
    * Add the found date in form YYYY-MM-DD as a prefix to the document title
    * If there is no date information in the document, use {current_date}
    * Use the form: date sender title
  # The prompt part will be appended if the date should not be included in the title using with_date: false
  no_date: |
    * Use the form: sender title
  # The prompt before the content of the document will be appended
  pre_content: |
    ### Begin of text ###
  # The prompt after the content of the document will be appended
  post_content: |
    ### End of text ###
```
