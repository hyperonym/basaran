# Basaran

Basaran is an open source alternative to the [OpenAI text completion API](https://platform.openai.com/docs/api-reference/completions/create). It provides a compatible streaming API for your [🤗 Transformers](https://huggingface.co/docs/transformers/index)-based [text generation models](https://huggingface.co/models?pipeline_tag=text-generation&sort=downloads).

![Playground demo](https://github.com/hyperonym/basaran/blob/master/docs/assets/demo.gif?raw=true)

## Roadmap

- [x] API
    - [x] Models
        - [x] List models
        - [x] Retrieve model
    - [x] Completions
        - [x] Create completion
    - [ ] Chat
        - [ ] Create chat completion
- [x] Model
    - [x] Architectures
        - [x] Encoder-decoder
        - [x] Decoder-only
    - [x] Decoding strategies
        - [x] Random sampling with temperature
        - [x] Nucleus-sampling (top-p)
        - [ ] Contrastive search

See the [open issues](https://github.com/hyperonym/basaran/issues) for a full list of proposed features.

## Contributing

This project is open-source. If you have any ideas or questions, please feel free to reach out by creating an issue!

Contributions are greatly appreciated, please refer to [CONTRIBUTING.md](https://github.com/hyperonym/basaran/blob/master/CONTRIBUTING.md) for more information.

## License

Basaran is available under the [MIT License](https://github.com/hyperonym/basaran/blob/master/LICENSE).

---

© 2023 [Hyperonym](https://hyperonym.org)
