async function encryptStr(secret, strToEncrypt) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoder = new TextEncoder();
    const keyData = encoder.encode(secret);
    const key = await crypto.subtle.importKey(
        "raw",
        keyData,
        { name: "AES-GCM" },
        false,
        ["encrypt"]
    );
    const encodedParams = encoder.encode(strToEncrypt);
    const ciphertext = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        key,
        encodedParams
    );
    const tagLength = 16; // AES-GCM 默认 128-bit tag
    const encryptedArray = new Uint8Array([...iv, ...new Uint8Array(ciphertext)]);
    return btoa(String.fromCharCode(...encryptedArray));
}


async function encryptObj(secret, objToEncrypt) {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoder = new TextEncoder();
    const keyData = encoder.encode(secret);
    const key = await crypto.subtle.importKey(
        "raw",
        keyData,
        { name: "AES-GCM" },
        false,
        ["encrypt"]
    );
    const encodedParams = encoder.encode(JSON.stringify(objToEncrypt));
    const ciphertext = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        key,
        encodedParams
    );
    const tagLength = 16; // AES-GCM 默认 128-bit tag
    const encryptedArray = new Uint8Array([...iv, ...new Uint8Array(ciphertext)]);
    return btoa(String.fromCharCode(...encryptedArray));
}


export default {
    async fetch(request, env, ctx) {
        let arrayBuffer, fileType, fileSize;

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
                msg: 'Method Not Allowed'
            }), {status: 405, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
        }

        // 定义失败响应
        const MISSING_PARAMS_RESPONSE = new Response(JSON.stringify({
            success: false,
            code: 400,
            msg: 'Missing r2 params or file'
        }), {status: 400, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
        const INVALID_PARAMS_RESPONSE = new Response(JSON.stringify({
            success: false,
            code: 400,
            msg: 'Invalid r2 params or file'
        }), {status: 400, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
        const FILE_OVERSIZE_RESPONSE = new Response(JSON.stringify({
            success: false,
            code: 400,
            msg: 'File size exceeds limit'
        }), {status: 400, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
        const R2_METHOD_NOT_ALLOWED_RESPONSE = new Response(JSON.stringify({
            success: false,
            code: 405,
            msg: 'R2 method not allowed'
        }), {status: 405, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
        const R2_OPERATION_FAILED_RESPONSE = new Response(JSON.stringify({
            success: false,
            code: 500,
            msg: 'R2 operation failed'
        }), {status: 500, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
        const EXPIRED_PARAMS_RESPONSE = new Response(JSON.stringify({
            success: false,
            code: 400,
            msg: 'R2 params expired'
        }), {status: 400, headers: {...corsHeaders, 'Content-Type': 'application/json'}});

        // 读取请求体
        const formData = await request.formData();
        const r2ParamsEncrypted = formData.get('r2_params');
        const file = formData.get('file');
        const fileExists = file !== null;
        if (fileExists) {
            arrayBuffer = await file.arrayBuffer(); // 转换为 ArrayBuffer 以便存储或传输
            fileType = file.type; // 获取 MIME 类型
            fileSize = arrayBuffer.byteLength; // 获取文件大小
        }

        // 检查请求是否携带 r2 params
        if (!r2ParamsEncrypted) {
            return MISSING_PARAMS_RESPONSE;
        }

        // 解密 r2 params
        let r2Params;
        try {
            const key = await crypto.subtle.importKey(
                "raw",
                new TextEncoder().encode(env.AES_GCM_SECRET),
                {name: "AES-GCM"},
                false,
                ["decrypt"]
            );
            let encryptedData = Uint8Array.from(atob(r2ParamsEncrypted), c => c.charCodeAt(0));
            let iv = encryptedData.slice(0, 12);
            let ciphertext = encryptedData.slice(12, -16);
            let tag = encryptedData.slice(-16);
            let decrypted = await crypto.subtle.decrypt(
                {name: "AES-GCM", iv: iv},
                key,
                new Uint8Array([...ciphertext, ...tag])
            );
            r2Params = JSON.parse(new TextDecoder().decode(decrypted));
        } catch (e) {
            return INVALID_PARAMS_RESPONSE;
        }

        // 检查 r2 params 是否过期
        if (r2Params.expires < Math.floor(Date.now() / 1000)) {
            return EXPIRED_PARAMS_RESPONSE;
        }

        // 进行 R2 操作
        switch (r2Params.method) {
            case 'avatar':
                let r2Response, options, uploadFailed;
                const previousAvatarKey = r2Params.previous_avatar_key;
                const verboseFeedback = r2Params.verbose_feedback;
                const MAX_AVATAR_SIZE = r2Params.max_size;
                const expectedFileType = r2Params.mime_type;
                if (!fileExists) {
                    return MISSING_PARAMS_RESPONSE;
                }
                if (fileType !== expectedFileType) {
                    return INVALID_PARAMS_RESPONSE;
                }
                if (parseInt(fileSize) > MAX_AVATAR_SIZE) {
                    return FILE_OVERSIZE_RESPONSE;
                }
                if (previousAvatarKey) {
                    let r2Response;
                    try {
                        r2Response = await env.WEB_BUCKET.head(previousAvatarKey);
                    } catch (e) {
                        if (!verboseFeedback) {
                            return R2_OPERATION_FAILED_RESPONSE;
                        } else {
                            return new Response(JSON.stringify({
                                success: false,
                                code: 500,
                                msg: `Failed to fetch previous avatar metadata: ${e.message}`
                            }), {status: 500, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
                        }
                    }
                    if (r2Response) {
                        try {
                            await env.WEB_BUCKET.delete(previousAvatarKey);
                        } catch (e) {
                            if (!verboseFeedback) {
                                return R2_OPERATION_FAILED_RESPONSE;
                            } else {
                                return new Response(JSON.stringify({
                                    success: false,
                                    code: 500,
                                    msg: `Failed to delete previous avatar: ${e.message}`
                                }), {status: 500, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
                            }
                        }
                    } else {
                        if (!verboseFeedback) {
                            return R2_OPERATION_FAILED_RESPONSE;
                        } else {
                            return new Response(JSON.stringify({
                                success: false,
                                code: 404,
                                msg: 'Previous avatar not found'
                            }), {status: 404, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
                        }
                    }
                }
                options = {
                    httpMetadata: {
                        contentType: fileType || 'application/octet-stream'
                    },
                    storageClass: 'Standard'
                }
                try {
                    r2Response = await env.WEB_BUCKET.put(r2Params.key, arrayBuffer, options);
                } catch (e) {
                    uploadFailed = true;
                }
                if (!r2Response || uploadFailed) {
                    if (!verboseFeedback) {
                        return R2_OPERATION_FAILED_RESPONSE;
                    } else {
                        return new Response(JSON.stringify({
                            success: false,
                            code: 500,
                            msg: 'Failed to upload avatar'
                        }), {status: 500, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
                    }
                }
                const avatarKey = r2Response.key
                const encryptedAvatarKey = await encryptStr(env.AES_GCM_SECRET, avatarKey);
                if (verboseFeedback) {
                    return new Response(JSON.stringify({
                        success: true,
                        key: encryptedAvatarKey,
                        r2_object: r2Response,
                        code: 200
                    }), {status: 200, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
                } else {
                    return new Response(JSON.stringify({
                        success: true,
                        key: encryptedAvatarKey,
                        code: 200
                    }), {status: 200, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
                }
            case 'head':

            case 'get':

            case 'put':

            case 'delete':

            case 'list':

            default:
                return new Response(JSON.stringify({
                    success: false,
                    code: 405,
                    msg: `Method ${r2Params.method} not allowed`
                }), {status: 405, headers: {...corsHeaders, 'Content-Type': 'application/json'}});
        }
    }
};
