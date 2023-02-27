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
        if (x < this.min) {
            x = this.min;
        }
        if (x > this.max) {
            x = this.max;
        }
        return x;
    }
}

class Field {
    constructor(key, label, type, defaultValue, bound) {
        this.key = key;
        this.label = label;
        this.type = type;
        this.defaultValue = defaultValue;
        this.bound = bound;
    }
    clamp(x) {
        if (typeof (x) == "string") {
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
        });

        range.addEventListener("input", () => {
            let x = field.clamp(range.value);
            input.value = x;
            range.value = x;
        });

        this.field = field;
        this.input = input;
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

        this.field = field;
        this.input = input;
    }
    get value() {
        return this.input.checked;
    }
}

class Handles {
    constructor(fields, container) {
        this.handles = fields.map(field => {
            switch (field.type) {
                case "number":
                    return new NumberHandle(field, container);
                case "boolean":
                    return new BooleanHandle(field, container);
                default:
                    throw new Error(`unknown field type: ${field.type}`);
            }
        });
    }
    get options() {
        let options = {};
        this.handles.forEach(handle => {
            options[handle.field.key] = handle.value;
        });
        return options;
    }
}

class Completion {
    constructor(prompt, options, inspector, container) {
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

        let params = [
            "prompt=" + encodeURIComponent(prompt),
            "stream=true",
            "logprobs=5"
        ];
        for (let key in options) {
            params.push(`${key}=${options[key]}`);
        }

        this.eventSource = new EventSource("/v1/completions?" + params.join("&"));
        this.eventSource.addEventListener("error", event => {
            this.clear();
            let error = createChild(container, "div");
            error.classList.add("pg-error");
            error.textContent = "An error occurred while attempting to connect.";
        });
        this.eventSource.addEventListener("message", event => {
            if (event.data == "[DONE]") {
                this.eventSource.close();
                return;
            }

            let data = JSON.parse(event.data);
            data.choices.forEach(choice => {
                let completion = this.completions[choice.index];
                let graphemes = [...choice.text];
                let logprobs = choice.logprobs;
                if (choice.finish_reason !== null) {
                    completion.dataset.finish = choice.finish_reason;
                }
                for (let i = 0; i < logprobs.tokens.length; i++) {
                    let text = "";
                    let start = logprobs.text_offset[i] - logprobs.text_offset[0];
                    if (i + 1 < logprobs.tokens.length) {
                        let end = logprobs.text_offset[i + 1] - logprobs.text_offset[0];
                        text = graphemes.slice(start, end).join("");
                    } else {
                        text = graphemes.slice(start).join("");
                    }

                    let info = {
                        "token": logprobs.tokens[i],
                        "token_logprob": logprobs.token_logprobs[i],
                        "top_logprobs": logprobs.top_logprobs[i]
                    };

                    let span = createChild(completion, "span");
                    let prob = Math.exp(logprobs.token_logprobs[i]);
                    span.textContent = text;
                    span.setAttribute("style", `background-color: rgba(70, 120, 220, ${0.25 * prob})`);
                    span.addEventListener("click", () => {
                        this.inspector.inspect(info);
                    });
                }
            });
        });
    }
    close() {
        this.eventSource.close();
    }
    clear() {
        this.close();
        this.container.replaceChildren();
    }
}

class Inspector {
    constructor(container) {
        this.container = container;
    }
    inspect(info) {
        // TODO(peakji): implement probability inspection.
    }
    clear() {
        this.container.replaceChildren();
    }
}

(function () {
    let fields = [
        new Field("temperature", "Temperature", "number", 0.7, new Bound(0, 1, 0.01)),
        new Field("top_p", "Top P", "number", 0.6, new Bound(0, 1, 0.01)),
        new Field("max_tokens", "Maximum length", "number", 256, new Bound(1, 4000, 1)),
        new Field("min_tokens", "Minimum length", "number", 1, new Bound(1, 500, 1)),
        new Field("n", "Number of completions", "number", 1, new Bound(1, 5, 1)),
        new Field("echo", "Echo prompt tokens", "boolean", false)
    ];

    let handles = new Handles(fields, document.querySelector(".pg-options"));
    let inspector = new Inspector(document.querySelector(".pg-probabilities"));

    let prompt = document.querySelector(".pg-prompt");
    let outputs = document.querySelector(".pg-outputs");

    let completion = null;
    document.querySelector(".pg-submit").addEventListener("click", () => {
        if (completion !== null) {
            completion.clear();
            inspector.clear();
        }
        completion = new Completion(prompt.textContent.trim(), handles.options, inspector, outputs);
    });

    document.querySelector(".pg-clear-prompt").addEventListener("click", () => {
        prompt.textContent = "";
    });

    document.querySelector(".pg-clear-completions").addEventListener("click", () => {
        if (completion !== null) {
            completion.clear();
            inspector.clear();
        }
    });
})();