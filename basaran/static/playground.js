function createChild(parent, tagName) {
    let element = document.createElement(tagName);
    parent.appendChild(element);
    return element;
}

class Bound {
    constructor(min, max, step) {
        this.min = min;
        this.max = max;
        this.step = step;
    }
    clamp(x) {
        let d = 1 / this.step;
        x = Math.round(x * d) / d;
        x = Math.max(x, this.min);
        x = Math.min(x, this.max);
        return x;
    }
}

class Field {
    constructor(
        key,
        label,
        type,
        defaultValue,
        props = {},
        onSet = () => void 0
    ) {
        this.key = key;
        this.label = label;
        this.type = type;
        this.defaultValue = defaultValue;
        this.onSet = onSet;

        Object.assign(this, props);
    }
    clamp(x) {
        if (typeof x == "string") {
            x = parseFloat(x);
        }
        if (isNaN(x)) {
            x = this.defaultValue;
        }
        return this.bound.clamp(x);
    }
}

class NumberHandle {
    constructor(field, container) {
        let option = createChild(container, "div");
        option.classList.add("pg-option");

        let tuple = createChild(option, "div");
        tuple.classList.add("pg-option-tuple");

        let label = createChild(tuple, "span");
        label.classList.add("pg-option-label");
        label.textContent = field.label;

        let input = createChild(tuple, "input");
        input.classList.add("pg-option-number-input");
        input.setAttribute("type", "text");
        input.value = field.defaultValue;

        let extra = createChild(option, "div");
        extra.classList.add("pg-option-extra");

        let range = createChild(extra, "input");
        range.classList.add("pg-option-number-range");
        range.setAttribute("type", "range");
        range.setAttribute("min", field.bound.min);
        range.setAttribute("max", field.bound.max);
        range.setAttribute("step", field.bound.step);
        range.value = field.defaultValue;

        input.addEventListener("change", () => {
            let x = field.clamp(input.value);
            input.value = x;
            range.value = x;

            field.onSet(input.value);
        });

        range.addEventListener("input", () => {
            let x = field.clamp(range.value);
            input.value = x;
            range.value = x;

            field.onSet(input.value);
        });

        this.field = field;
        this.input = input;
        this.range = range;
    }

    set(value) {
        let x = this.field.clamp(value);
        this.input.value = x;
        this.range.value = x;
    }

    get value() {
        return this.field.clamp(this.input.value);
    }
}

class BooleanHandle {
    constructor(field, container) {
        let option = createChild(container, "div");
        option.classList.add("pg-option");

        let tuple = createChild(option, "div");
        tuple.classList.add("pg-option-tuple");

        let label = createChild(tuple, "span");
        label.classList.add("pg-option-label");
        label.textContent = field.label;

        let input = createChild(tuple, "input");
        input.classList.add("pg-option-boolean-input");
        input.setAttribute("type", "checkbox");
        input.checked = field.defaultValue;

        input.addEventListener("input", () => {
            field.onSet(input.checked);
        });

        this.field = field;
        this.input = input;
    }

    set(value) {
        this.input.checked = value;
    }

    get value() {
        return this.input.checked;
    }
}

class SelectHandle {
    constructor(field, container) {
        let option = createChild(container, "div");
        option.classList.add("pg-option");

        let tuple = createChild(option, "div");
        tuple.classList.add("pg-option-tuple");

        let label = createChild(tuple, "span");
        label.classList.add("pg-option-label");
        label.textContent = field.label;

        let input = createChild(tuple, "select");
        input.classList.add("pg-option-select-input");
        input.value = field.defaultValue;

        for (let option of field.options) {
            let opt = createChild(input, "option");
            opt.value = option.value;
            opt.textContent = option.label;
        }

        input.addEventListener("input", () => {
            field.onSet(input.value);
        });

        this.field = field;
        this.input = input;
    }

    set(value) {
        this.input.value = value;
    }

    get value() {
        return this.input.value;
    }
}

class Handles {
    constructor(fields, container) {
        this.handles = fields.map((field) => {
            switch (field.type) {
                case "number":
                    return new NumberHandle(field, container);
                case "boolean":
                    return new BooleanHandle(field, container);
                case "select":
                    return new SelectHandle(field, container);
                default:
                    throw new Error(`unknown field type: ${field.type}`);
            }
        });
    }

    set(options) {
        for (let key in options) {
            this.handles
                .find((handle) => handle.field.key === key)
                ?.set(options[key]);
        }
    }

    get options() {
        let options = {};
        this.handles.forEach((handle) => {
            if (!handle.field.noSend) {
                options[handle.field.key] = handle.value;
            }
        });
        return options;
    }
}

class Completion extends EventTarget {
    constructor(prompt, options, inspector, container) {
        super();

        this.inspector = inspector;
        this.container = container;
        this.completions = [];
        for (let i = 0; i < options.n; i++) {
            let completion = createChild(container, "div");
            completion.classList.add("pg-completion");
            completion.dataset.index = i + 1;
            completion.dataset.finish = "none";
            this.completions.push(completion);
        }

        let highlight = options.highlight === true;
        delete options.highlight;

        let params = [
            "prompt=" + encodeURIComponent(prompt),
            "stream=true",
            "logprobs=5",
        ];
        for (let key in options) {
            params.push(`${key}=${options[key]}`);
        }

        this.eventSource = new EventSource(
            "/v1/completions?" + params.join("&")
        );
        this.eventSource.addEventListener("error", (event) => {
            this.stop();
            let error = createChild(container, "div");
            error.classList.add("pg-error");
            error.textContent =
                "An error occurred while attempting to connect.";
        });
        this.eventSource.addEventListener("message", (event) => {
            if (event.data == "[DONE]") {
                this.eventSource.close();
                this.dispatchEvent(new CustomEvent("done"));
                return;
            }

            let data = JSON.parse(event.data);
            data.choices.forEach((choice) => {
                let completion = this.completions[choice.index];
                let graphemes = [...choice.text];

                let logprobs = choice.logprobs;
                if (choice.finish_reason !== null) {
                    completion.dataset.finish = choice.finish_reason;
                }
                for (let i = 0; i < logprobs.tokens.length; i++) {
                    let text = "";
                    let start =
                        logprobs.text_offset[i] - logprobs.text_offset[0];
                    if (i + 1 < logprobs.tokens.length) {
                        let end =
                            logprobs.text_offset[i + 1] -
                            logprobs.text_offset[0];
                        text = graphemes.slice(start, end).join("");
                    } else {
                        text = graphemes.slice(start).join("");
                    }

                    let info = {
                        token: logprobs.tokens[i],
                        token_logprob: logprobs.token_logprobs[i],
                        top_logprobs: logprobs.top_logprobs[i],
                    };

                    let span = createChild(completion, "span");
                    let prob = Math.exp(logprobs.token_logprobs[i]);
                    span.textContent = text;
                    span.addEventListener("click", () => {
                        this.inspector.inspect(info);
                    });
                    if (highlight) {
                        span.setAttribute(
                            "style",
                            `background-color: rgba(70, 120, 220, ${0.5 * prob})`
                        );
                    }
                }
            });
        });
    }

    get running() {
        return this.eventSource.readyState !== EventSource.CLOSED;
    }

    stop() {
        for (const completion of this.completions) {
            completion.dataset.finish = "user";
        }
        this.eventSource.close();
        this.dispatchEvent(new CustomEvent("done"));
    }

    clear() {
        this.stop();
        this.container.replaceChildren();
    }
}

class Inspector {
    constructor(container) {
        this.container = container;
    }
    inspect(info) {
        this.clear();

        let top = [];
        for (let token in info.top_logprobs) {
            top.push({
                token: token,
                prob: Math.min(Math.exp(info.top_logprobs[token]), 1.0),
            });
        }

        top.sort((a, b) => b.prob - a.prob).forEach((x) => {
            let sample = createChild(this.container, "div");
            sample.classList.add("pg-sample");

            let tuple = createChild(sample, "div");
            tuple.classList.add("pg-sample-tuple");

            let text = createChild(tuple, "div");
            text.classList.add("pg-sample-text");
            text.textContent = x.token;

            let probability = createChild(tuple, "div");
            probability.classList.add("pg-sample-probability");
            probability.textContent = (x.prob * 100).toFixed(2) + "%";

            if (x.token == info.token) {
                text.classList.add("pg-highlight-text");
                probability.classList.add("pg-highlight-text");
            }

            let bar = createChild(sample, "div");
            bar.classList.add("pg-sample-bar");

            let fill = createChild(bar, "div");
            fill.classList.add("pg-sample-bar-fill");
            fill.setAttribute("style", `width:${x.prob * 100}%;`);
        });
    }
    clear() {
        this.container.replaceChildren();
    }
}

(async function () {
    let presets = await fetch("static/presets.json")
        .then((res) => res.json())
        .catch(() => []);

    let onPreset = (presetId) => {
        handles.set(presets.find((preset) => preset.id === presetId) ?? {});
    };

    let fields = [
        new Field(
            "preset",
            "Preset",
            "select",
            presets[0].id,
            {
                noSend: true,
                options: presets.map((preset) => ({
                    value: preset.id,
                    label: preset.name,
                })),
            },
            onPreset
        ),

        new Field("temperature", "Temperature", "number", 0.7, {
            bound: new Bound(0, 2, 0.01),
        }),
        new Field("top_p", "Top P", "number", 0.95, {
            bound: new Bound(0, 1, 0.01),
        }),
        new Field("max_tokens", "Maximum length", "number", 256, {
            bound: new Bound(1, 4000, 1),
        }),
        new Field("min_tokens", "Minimum length", "number", 1, {
            bound: new Bound(1, 500, 1),
        }),
        new Field("n", "Number of completions", "number", 1, {
            bound: new Bound(1, 5, 1),
        }),
        new Field("echo", "Echo prompt tokens", "boolean", false),
        new Field("highlight", "Token highlighting", "boolean", false),
    ];

    let handles = new Handles(fields, document.querySelector(".pg-options"));
    let inspector = new Inspector(document.querySelector(".pg-inspector"));
    let completion = null;

    handles.set(presets[0]);

    let submit = document.querySelector(".pg-submit");
    let prompt = document.querySelector(".pg-prompt");
    let outputs = document.querySelector(".pg-outputs");

    submit.addEventListener("click", (e) => {
        if (completion) {
            if (completion.running) {
                completion.stop();
                return;
            }

            completion.clear();
        }

        inspector.clear();

        e.target.textContent = "Stop";
        e.target.dataset.state = "stop";

        completion = new Completion(
            prompt.value,
            handles.options,
            inspector,
            outputs
        );
        completion.addEventListener("done", () => {
            e.target.textContent = "Submit";
            e.target.dataset.state = "submit";
        });
    });

    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key == "Enter") {
            e.preventDefault();
            submit.click();
        }
    });

    let resizePrompt = () => {
        prompt.style.height = 0;
        prompt.style.height = prompt.scrollHeight + "px";
    };

    document.querySelector(".pg-clear-prompt").addEventListener("click", () => {
        prompt.value = "";
        resizePrompt();
    });

    document
        .querySelector(".pg-clear-completions")
        .addEventListener("click", () => {
            if (completion !== null) {
                completion.clear();
                inspector.clear();
            }
        });

    prompt.addEventListener("input", resizePrompt);
    resizePrompt();
})();
