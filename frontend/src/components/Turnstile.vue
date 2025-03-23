<template>
  <div ref="turnstile"></div>
</template>

<script>
import { mapState } from 'vuex';
import { TURNSTILE_SITE_KEY } from "../config/constants";

export default {
  name: 'VueTurnstile',
  emits: ['update:cfToken', 'error', 'unsupported', 'expired', 'before-interactive', 'after-interactive'],
  props: {
    cfToken: {
      type: String,
      required: true,
    },
    resetInterval: {
      type: Number,
      required: false,
      default: 295 * 1000,
    },
    size: {
      type: String,
      required: false,
      default: 'normal',
    },
    theme: {
      type: String,
      required: false,
      default: 'auto',
    },
    language: {
      type: String,
      required: false,
      default: 'auto',
    },
    action: {
      type: String,
      required: false,
      default: '',
    },
    appearance: {
      type: String,
      required: false,
      default: 'always',
    },
    renderOnMount: {
      type: Boolean,
      required: false,
      default: true,
    }
  },
  data() {
    return {
      resetTimeout: undefined,
      widgetId: undefined,
    };
  },
  computed: {
    ...mapState(['fingerprint']),
    turnstileOptions() {
      return {
        sitekey: TURNSTILE_SITE_KEY,
        theme: this.theme,
        language: this.language,
        size: this.size,
        callback: this.callback,
        action: this.action,
        appearance: this.appearance,
        cData: this.fingerprint,
        'error-callback': this.errorCallback,
        'expired-callback': this.expiredCallback,
        'unsupported-callback': this.unsupportedCallback,
        'before-interactive-callback': this.beforeInteractiveCallback,
        'after-interactive-callback': this.afterInteractivecallback,
      };
    },
  },
  methods: {
    afterInteractivecallback() {
      this.$emit('after-interactive');
    },
    beforeInteractiveCallback() {
      this.$emit('before-interactive');
    },
    expiredCallback() {
      this.$emit('expired');
    },
    unsupportedCallback() {
      this.$emit('unsupported');
    },
    errorCallback(code) {
      this.$emit('error', code);
    },
    callback(token) {
      this.$emit('update:cfToken', token);
      this.startResetTimeout();
    },
    reset() {
      if (window.turnstile) {
        this.$emit('update:cfToken', '');
        try {
          window.turnstile.reset();
        } catch (e) {
          console.error('Failed to reset Turnstile:', e);
        }
      }
    },

    remove() {
      if (this.widgetId) {
        window.turnstile.remove(this.widgetId);
        this.widgetId = undefined;
      }
    },

    render() {
      this.widgetId = window.turnstile.render(this.$refs.turnstile, this.turnstileOptions);
    },

    startResetTimeout() {
      this.resetTimeout = setTimeout(() => {
        this.reset();
      }, this.resetInterval);
    },
  },
  async mounted() {
    const turnstileSrc = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
    const turnstileLoadFunction = 'cfTurnstileOnLoad';
    let turnstileState = typeof window !== 'undefined' ? (window.turnstile !== undefined ? 'ready' : 'unloaded') : 'unloaded';
    let turnstileLoad;

    const turnstileLoadPromise = new Promise((resolve, reject) => {
      turnstileLoad = { resolve, reject };
      if (turnstileState === 'ready') resolve();
    });

    window[turnstileLoadFunction] = () => {
      turnstileLoad.resolve();
      turnstileState = 'ready';
    };

    const ensureTurnstile = () => {
      if (turnstileState === 'unloaded') {
        turnstileState = 'loading';
        const url = `${turnstileSrc}?onload=${turnstileLoadFunction}&render=explicit`;
        const script = document.createElement('script');
        script.src = url;
        script.async = true;
        script.addEventListener('error', () => {
          turnstileLoad.reject('Failed to load Turnstile.');
        });
        document.head.appendChild(script);
      }
      return turnstileLoadPromise;
    };

    await ensureTurnstile();

    if (this.renderOnMount) {
      this.render();
    }
  },

  beforeUnmount() {
    this.remove();
    clearTimeout(this.resetTimeout);
  },
};
</script>
