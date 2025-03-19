// noinspection DuplicatedCode

async function encryptObj(secret, objToEncrypt) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoder = new TextEncoder();
    const keyData = encoder.encode(secret);
    const key = await crypto.subtle.importKey(
        "raw",
        keyData,
        {name: "AES-GCM"},
        false,
        ["encrypt"]
    );
    const encodedParams = encoder.encode(JSON.stringify(objToEncrypt));
    const ciphertext = await crypto.subtle.encrypt(
        {name: "AES-GCM", iv: iv},
        key,
        encodedParams
    );
    const tagLength = 16; // AES-GCM 默认 128-bit tag
    const encryptedArray = new Uint8Array([...iv, ...new Uint8Array(ciphertext)]);
    return btoa(String.fromCharCode(...encryptedArray));
}


export default {
    async fetch(request, env, ctx) {
        try {
            // 设置 CORS 政策
            const allowedOrigins = ['http://localhost', /\.dowdah\.com$/];
            let origin = request.headers.get('Origin');
            let allowedOrigin = allowedOrigins.some(o => typeof o === 'string' ? o === origin : o.test(origin)) ? origin : '*';
            let corsHeaders = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Content-Length, Authorization'
            };
            corsHeaders['Access-Control-Allow-Origin'] = allowedOrigin;
            if (request.method === 'OPTIONS') {
                return new Response(null, {status: 204, headers: corsHeaders});
            }

            // 限制请求方法为 POST
            if (request.method !== 'POST') {
                return new Response(JSON.stringify({
                    success: false,
                    code: 405,
                    msg: 'Method not allowed'
                }), {status: 405, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
            }

            // 定义失败响应
            const INVALID_PARAMS_RESPONSE = new Response(JSON.stringify({
                success: false,
                code: 400,
                msg: 'Invalid parameters'
            }), {status: 400, headers: {...corsHeaders, 'Content-Type': 'application/json'}});

            const CF_FAILURE_RESPONSE = new Response(JSON.stringify({
                success: false,
                code: 400,
                msg: 'Cloudflare verification failed'
            }), {status: 400, headers: {...corsHeaders, 'Content-Type': 'application/json'}});

            // 从请求中获取参数
            let formData, token;
            if (!request.headers.has('Content-Type')) {
                return INVALID_PARAMS_RESPONSE;
            }
            if (request.headers.get('Content-Type').indexOf('json') !== -1) {
                formData = JSON.stringify(formData);
            } else if (request.headers.get('Content-Type').indexOf('form') !== -1) {
                formData = await request.formData();
            } else {
                return INVALID_PARAMS_RESPONSE;
            }
            if (formData && formData.has('token')) {
                token = formData.get('token');
            } else {
                return INVALID_PARAMS_RESPONSE;
            }

            const url = "https://challenges.cloudflare.com/turnstile/v0/siteverify";
            let payload = new FormData();
            payload.append('secret', env.SECRET);
            payload.append('response', token);
            payload.append('remoteip', request.headers.get('CF-Connecting-IP'));
            const response = await fetch(url, {
                method: 'POST',
                body: payload
            });
            if (!response.ok) {
                return CF_FAILURE_RESPONSE;
            } else {
                const data = await response.json();
                if (!data.success) {
                    return CF_FAILURE_RESPONSE;
                } else {
                    const encryptedData = await encryptObj(env.AES_GCM_SECRET, data);
                    return new Response(JSON.stringify({
                        success: true,
                        code: 200,
                        cfResponse: encryptedData,
                    }), {status: 200, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
                }
            }
        } catch (error) {
            return new Response(JSON.stringify({
                success: false,
                code: 500,
                msg: `Unknown error: ${error}`
            }), {status: 500, headers: {'Content-Type': 'application/json'}});
        }
    }
};
