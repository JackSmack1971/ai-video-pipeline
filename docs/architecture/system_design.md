# System Architecture

The AI Video Pipeline is composed of modular services connected through asynchronous queues.

```
User -> API Server -> Idea Generator
                         |--> Image Generator
                         |--> Video Generator
                         |--> Music Generator
                         |--> Voice Generator
                         v
                     Composer -> Storage
```

Each service uses environment variables for credentials and validates user input. Retry logic is implemented for all external API calls to ensure reliability.
