import axios from 'axios';

const FASTAPI_URL = 'http://127.0.0.1:8000';

export const stegoService = {
  async getCapacity(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);

    const response = await axios.post(`${FASTAPI_URL}/capacity`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async encodeMessage(imageFile, message) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);

    const response = await axios.post(`${FASTAPI_URL}/encode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob', // Expect PNG binary stream
    });

    const payloadBytes = response.headers['x-payload-bytes'];
    const capacityTotalBytes = response.headers['x-capacity-total-bytes'];
    const capacityUsedPercent = response.headers['x-capacity-used-percent'];
    const bpp = response.headers['x-bits-per-pixel'];

    // Quality metrics headers
    const psnr = response.headers['x-metric-psnr'];
    const ssim = response.headers['x-metric-ssim'];
    const mse = response.headers['x-metric-mse'];
    const rating = response.headers['x-metric-rating'];
    const isImperceptible = response.headers['x-metric-imperceptible'] === 'true';

    return {
      blob: response.data,
      metadata: {
        payloadBytes: payloadBytes ? parseInt(payloadBytes, 10) : 0,
        capacityTotalBytes: capacityTotalBytes ? parseInt(capacityTotalBytes, 10) : 0,
        capacityUsedPercent: capacityUsedPercent ? parseFloat(capacityUsedPercent) : 0,
        bpp: bpp ? parseFloat(bpp) : 0,
        psnr: psnr || 'N/A',
        ssim: ssim ? parseFloat(ssim) : null,
        mse: mse ? parseFloat(mse) : null,
        rating: rating || 'EXCELLENT',
        isImperceptible,
      },
    };
  },

  async decodeMessage(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);

    const response = await axios.post(`${FASTAPI_URL}/decode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async analyzeImage(imageFile, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/analyze`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async compareMetrics(coverFile, stegoFile, originalText = null, recoveredText = null, methodName = 'Baseline_LSB') {
    const formData = new FormData();
    formData.append('cover_image', coverFile);
    formData.append('stego_image', stegoFile);
    if (originalText) formData.append('original_payload', originalText);
    if (recoveredText) formData.append('recovered_payload', recoveredText);
    formData.append('method_name', methodName);
    formData.append('record_experiment', 'true');

    const response = await axios.post(`${FASTAPI_URL}/metrics/compare`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async getMetricsHistory() {
    const response = await axios.get(`${FASTAPI_URL}/metrics/history`);
    return response.data;
  },

  // Phase 10: Content-Adaptive Rule-Based Steganography
  async getAdaptiveCapacity(imageFile, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/adaptive/capacity`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async encodeAdaptiveMessage(imageFile, message, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/adaptive/encode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });

    const payloadBytes = response.headers['x-payload-bytes'];
    const capacityTotalBytes = response.headers['x-capacity-total-bytes'];
    const capacityUsedPercent = response.headers['x-capacity-used-percent'];
    const blocksUtilized = response.headers['x-blocks-utilized'];
    const blocksPreserved = response.headers['x-blocks-preserved'];
    const bpp = response.headers['x-bits-per-pixel'];
    const psnr = response.headers['x-metric-psnr'];
    const ssim = response.headers['x-metric-ssim'];
    const mse = response.headers['x-metric-mse'];
    const rating = response.headers['x-metric-rating'];
    const isImperceptible = response.headers['x-metric-imperceptible'] === 'true';

    return {
      blob: response.data,
      metadata: {
        payloadBytes: payloadBytes ? parseInt(payloadBytes, 10) : 0,
        capacityTotalBytes: capacityTotalBytes ? parseInt(capacityTotalBytes, 10) : 0,
        capacityUsedPercent: capacityUsedPercent ? parseFloat(capacityUsedPercent) : 0,
        blocksUtilized: blocksUtilized ? parseInt(blocksUtilized, 10) : 0,
        blocksPreserved: blocksPreserved ? parseInt(blocksPreserved, 10) : 0,
        bpp: bpp ? parseFloat(bpp) : 0,
        psnr: psnr || 'N/A',
        ssim: ssim ? parseFloat(ssim) : null,
        mse: mse ? parseFloat(mse) : null,
        rating: rating || 'EXCELLENT',
        isImperceptible,
        method: 'Adaptive_Rule_Based_LSB',
      },
    };
  },

  async decodeAdaptiveMessage(imageFile, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/adaptive/decode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async compareBaselineVsAdaptive(imageFile, message, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/adaptive/compare`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Phase 13: AI Region Suitability Classifier & Heatmap
  async getAiRegionInfo() {
    const response = await axios.get(`${FASTAPI_URL}/ai/region/info`);
    return response.data;
  },

  async analyzeImageRegions(imageFile, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/ai/region/analyze`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async getAiRegionHeatmap(imageFile, blockSize = 16, alpha = 0.40) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('block_size', blockSize);
    formData.append('alpha', alpha);

    const response = await axios.post(`${FASTAPI_URL}/ai/region/heatmap`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });

    const totalBlocks = response.headers['x-total-blocks'];
    const highTextureBlocks = response.headers['x-high-texture-blocks'];
    const mediumBlocks = response.headers['x-medium-blocks'];
    const smoothBlocks = response.headers['x-smooth-blocks'];
    const highTexturePercent = response.headers['x-high-texture-percent'];
    const smoothPercent = response.headers['x-smooth-percent'];
    const recCapacityBytes = response.headers['x-recommended-capacity-bytes'];

    return {
      blob: response.data,
      metadata: {
        totalBlocks: totalBlocks ? parseInt(totalBlocks, 10) : 0,
        highTextureBlocks: highTextureBlocks ? parseInt(highTextureBlocks, 10) : 0,
        mediumBlocks: mediumBlocks ? parseInt(mediumBlocks, 10) : 0,
        smoothBlocks: smoothBlocks ? parseInt(smoothBlocks, 10) : 0,
        highTexturePercent: highTexturePercent ? parseFloat(highTexturePercent) : 0,
        smoothPercent: smoothPercent ? parseFloat(smoothPercent) : 0,
        recommendedCapacityBytes: recCapacityBytes ? parseInt(recCapacityBytes, 10) : 0,
      },
    };
  },

  // Phase 14: AI-Selected Adaptive Steganography
  async getAiStegoCapacity(imageFile, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/ai-stego/capacity`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async encodeAiMessage(imageFile, message, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/ai-stego/encode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });

    const payloadBytes = response.headers['x-payload-bytes'];
    const capacityTotalBytes = response.headers['x-capacity-total-bytes'];
    const capacityUsedPercent = response.headers['x-capacity-used-percent'];
    const blocksUtilized = response.headers['x-blocks-utilized'];
    const blocksPreserved = response.headers['x-blocks-preserved'];
    const bpp = response.headers['x-bits-per-pixel'];
    const psnr = response.headers['x-metric-psnr'];
    const ssim = response.headers['x-metric-ssim'];
    const mse = response.headers['x-metric-mse'];
    const rating = response.headers['x-metric-rating'];
    const isImperceptible = response.headers['x-metric-imperceptible'] === 'true';

    return {
      blob: response.data,
      metadata: {
        payloadBytes: payloadBytes ? parseInt(payloadBytes, 10) : 0,
        capacityTotalBytes: capacityTotalBytes ? parseInt(capacityTotalBytes, 10) : 0,
        capacityUsedPercent: capacityUsedPercent ? parseFloat(capacityUsedPercent) : 0,
        blocksUtilized: blocksUtilized ? parseInt(blocksUtilized, 10) : 0,
        blocksPreserved: blocksPreserved ? parseInt(blocksPreserved, 10) : 0,
        bpp: bpp ? parseFloat(bpp) : 0,
        psnr: psnr || 'N/A',
        ssim: ssim ? parseFloat(ssim) : null,
        mse: mse ? parseFloat(mse) : null,
        rating: rating || 'EXCELLENT',
        isImperceptible,
        method: 'AI_Random_Forest_Adaptive_LSB',
      },
    };
  },

  async decodeAiMessage(imageFile, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/ai-stego/decode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async compareAllThreeMethods(imageFile, message, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/ai-stego/compare`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Phase 15: PRNG Key-Based Random Block Scatter Steganography
  async getScatterCapacity(imageFile, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/scatter/capacity`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async encodeScatterMessage(imageFile, message, stegoKey, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('stego_key', stegoKey);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/scatter/encode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });

    const payloadBytes = response.headers['x-payload-bytes'];
    const capacityTotalBytes = response.headers['x-capacity-total-bytes'];
    const capacityUsedPercent = response.headers['x-capacity-used-percent'];
    const blocksUtilized = response.headers['x-blocks-utilized'];
    const blocksPreserved = response.headers['x-blocks-preserved'];
    const bpp = response.headers['x-bits-per-pixel'];
    const keyFingerprint = response.headers['x-key-fingerprint'];
    const psnr = response.headers['x-metric-psnr'];
    const ssim = response.headers['x-metric-ssim'];
    const mse = response.headers['x-metric-mse'];
    const rating = response.headers['x-metric-rating'];
    const isImperceptible = response.headers['x-metric-imperceptible'] === 'true';

    return {
      blob: response.data,
      metadata: {
        payloadBytes: payloadBytes ? parseInt(payloadBytes, 10) : 0,
        capacityTotalBytes: capacityTotalBytes ? parseInt(capacityTotalBytes, 10) : 0,
        capacityUsedPercent: capacityUsedPercent ? parseFloat(capacityUsedPercent) : 0,
        blocksUtilized: blocksUtilized ? parseInt(blocksUtilized, 10) : 0,
        blocksPreserved: blocksPreserved ? parseInt(blocksPreserved, 10) : 0,
        bpp: bpp ? parseFloat(bpp) : 0,
        keyFingerprint: keyFingerprint || 'Unknown',
        psnr: psnr || 'N/A',
        ssim: ssim ? parseFloat(ssim) : null,
        mse: mse ? parseFloat(mse) : null,
        rating: rating || 'EXCELLENT',
        isImperceptible,
        method: 'Key_Scattered_AI_Adaptive_LSB',
      },
    };
  },

  async decodeScatterMessage(imageFile, stegoKey, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('stego_key', stegoKey);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/scatter/decode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async verifyStegoKey(imageFile, stegoKey, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('stego_key', stegoKey);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/scatter/verify-key`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Phase 16: Deep Learning Steganalyzer CNN
  async getSteganalyzerInfo() {
    const response = await axios.get(`${FASTAPI_URL}/ai/steganalyzer/info`);
    return response.data;
  },

  async detectStego(imageFile, threshold = null) {
    const formData = new FormData();
    formData.append('image', imageFile);
    if (threshold !== null && threshold !== undefined) {
      formData.append('threshold', threshold);
    }

    const response = await axios.post(`${FASTAPI_URL}/ai/steganalyzer/detect`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Phase 17: Adversarial Feedback-Optimized Steganography
  async encodeFeedbackMessage(imageFile, message, stegoKey, blockSize = 16, threshold = 0.35, maxIterations = 5) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('stego_key', stegoKey);
    formData.append('block_size', blockSize);
    formData.append('threshold', threshold);
    formData.append('max_iterations', maxIterations);

    const response = await axios.post(`${FASTAPI_URL}/ai-stego/feedback/encode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });

    const payloadBytes = response.headers['x-payload-bytes'];
    const blocksUtilized = response.headers['x-blocks-utilized'];
    const converged = response.headers['x-optimization-converged'] === 'true';
    const iterationsRun = response.headers['x-iterations-run'];
    const initialPStego = response.headers['x-initial-p-stego'];
    const finalPStego = response.headers['x-final-p-stego'];
    const pStegoReduction = response.headers['x-p-stego-reduction'];
    const psnr = response.headers['x-metric-psnr'];
    const ssim = response.headers['x-metric-ssim'];
    const mse = response.headers['x-metric-mse'];
    const rating = response.headers['x-metric-rating'];
    const isImperceptible = response.headers['x-metric-imperceptible'] === 'true';
    const keyFingerprint = response.headers['x-key-fingerprint'];

    return {
      blob: response.data,
      metadata: {
        payloadBytes: payloadBytes ? parseInt(payloadBytes, 10) : 0,
        blocksUtilized: blocksUtilized ? parseInt(blocksUtilized, 10) : 0,
        converged,
        iterationsRun: iterationsRun ? parseInt(iterationsRun, 10) : 1,
        initialPStego: initialPStego ? parseFloat(initialPStego) : 0,
        finalPStego: finalPStego ? parseFloat(finalPStego) : 0,
        pStegoReduction: pStegoReduction ? parseFloat(pStegoReduction) : 0,
        psnr: psnr || 'N/A',
        ssim: ssim ? parseFloat(ssim) : null,
        mse: mse ? parseFloat(mse) : null,
        rating: rating || 'EXCELLENT',
        isImperceptible,
        keyFingerprint: keyFingerprint || 'Unknown',
        method: 'AI_Feedback_Optimized_LSB',
      },
    };
  },

  async decodeFeedbackMessage(imageFile, stegoKey, blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('stego_key', stegoKey);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/ai-stego/feedback/decode`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async runFeedbackDryrun(imageFile, message, stegoKey, blockSize = 16, threshold = 0.35, maxIterations = 5) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('stego_key', stegoKey);
    formData.append('block_size', blockSize);
    formData.append('threshold', threshold);
    formData.append('max_iterations', maxIterations);

    const response = await axios.post(`${FASTAPI_URL}/ai-stego/feedback/dryrun`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Phase 18: One-Click End-to-End Stego Orchestration Pipeline
  async encodePipelineHybrid(imageFile, message, recipientPublicKey, stegoPassphrase = '', securityLevel = 'Balanced', blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('recipient_public_key', recipientPublicKey);
    if (stegoPassphrase) formData.append('stego_passphrase', stegoPassphrase);
    formData.append('security_level', securityLevel);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/pipeline/encode-hybrid`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });

    const coverSha256 = response.headers['x-cover-sha256'];
    const stegoSha256 = response.headers['x-stego-sha256'];
    const rawPayloadBytes = response.headers['x-payload-bytes'];
    const envelopeBytes = response.headers['x-envelope-bytes'];
    const level = response.headers['x-security-level'];
    const recipientFp = response.headers['x-recipient-fingerprint'];
    const converged = response.headers['x-optimization-converged'] === 'true';
    const iterationsRun = response.headers['x-iterations-run'];
    const initialPStego = response.headers['x-initial-p-stego'];
    const finalPStego = response.headers['x-final-p-stego'];
    const pStegoReduction = response.headers['x-p-stego-reduction'];
    const psnr = response.headers['x-metric-psnr'];
    const ssim = response.headers['x-metric-ssim'];
    const mse = response.headers['x-metric-mse'];
    const rating = response.headers['x-metric-rating'];
    const isImperceptible = response.headers['x-metric-imperceptible'] === 'true';
    const execTimeMs = response.headers['x-execution-time-ms'];

    return {
      blob: response.data,
      metadata: {
        coverSha256: coverSha256 || '',
        stegoSha256: stegoSha256 || '',
        rawPayloadBytes: rawPayloadBytes ? parseInt(rawPayloadBytes, 10) : 0,
        envelopeBytes: envelopeBytes ? parseInt(envelopeBytes, 10) : 0,
        securityLevel: level || 'Balanced',
        recipientFingerprint: recipientFp || 'Unknown',
        converged,
        iterationsRun: iterationsRun ? parseInt(iterationsRun, 10) : 1,
        initialPStego: initialPStego ? parseFloat(initialPStego) : 0,
        finalPStego: finalPStego ? parseFloat(finalPStego) : 0,
        pStegoReduction: pStegoReduction ? parseFloat(pStegoReduction) : 0,
        psnr: psnr || 'N/A',
        ssim: ssim ? parseFloat(ssim) : null,
        mse: mse ? parseFloat(mse) : null,
        rating: rating || 'EXCELLENT',
        isImperceptible,
        executionTimeMs: execTimeMs ? parseInt(execTimeMs, 10) : 0,
        method: 'One_Click_Hybrid_AI_Pipeline',
      },
    };
  },

  async decodePipelineHybrid(imageFile, recipientPrivateKey, stegoPassphrase = '', privateKeyPassphrase = '', blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('recipient_private_key', recipientPrivateKey);
    if (stegoPassphrase) formData.append('stego_passphrase', stegoPassphrase);
    if (privateKeyPassphrase) formData.append('private_key_passphrase', privateKeyPassphrase);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/pipeline/decode-hybrid`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async dryrunPipelineHybrid(imageFile, message, recipientPublicKey, stegoPassphrase = '', securityLevel = 'Balanced', blockSize = 16) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('message', message);
    formData.append('recipient_public_key', recipientPublicKey);
    if (stegoPassphrase) formData.append('stego_passphrase', stegoPassphrase);
    formData.append('security_level', securityLevel);
    formData.append('block_size', blockSize);

    const response = await axios.post(`${FASTAPI_URL}/pipeline/dryrun-hybrid`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Phase 19: Robustness & Noise Perturbation Profiling
  async perturbImage(imageFile, attackType = 'gaussian', params = {}) {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('attack_type', attackType);
    if (params.std !== undefined) formData.append('std', params.std);
    if (params.mean !== undefined) formData.append('mean', params.mean);
    if (params.density !== undefined) formData.append('density', params.density);
    if (params.saltVsPepper !== undefined) formData.append('salt_vs_pepper', params.saltVsPepper);
    if (params.quality !== undefined) formData.append('quality', params.quality);
    if (params.kernelSize !== undefined) formData.append('kernel_size', params.kernelSize);
    if (params.sigma !== undefined) formData.append('sigma', params.sigma);
    if (params.seed !== undefined && params.seed !== null) formData.append('seed', params.seed);

    const response = await axios.post(`${FASTAPI_URL}/robustness/perturb`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });

    const degradedPsnr = response.headers['x-degraded-psnr'];
    const degradedSsim = response.headers['x-degraded-ssim'];
    const degradedMse = response.headers['x-degraded-mse'];
    const lsbBer = response.headers['x-lsb-ber'];
    const qualityRating = response.headers['x-quality-rating'];
    const attackIntensity = response.headers['x-attack-intensity'];

    return {
      blob: response.data,
      metadata: {
        attackType,
        attackIntensity: attackIntensity ? parseFloat(attackIntensity) : 0,
        degradedPsnr: degradedPsnr || 'N/A',
        degradedSsim: degradedSsim ? parseFloat(degradedSsim) : null,
        degradedMse: degradedMse ? parseFloat(degradedMse) : null,
        lsbBer: lsbBer ? parseFloat(lsbBer) : 0,
        qualityRating: qualityRating || 'GOOD',
      },
    };
  },

  async getDifferenceMap(origFile, pertFile, amplification = 10.0) {
    const formData = new FormData();
    formData.append('original_image', origFile);
    formData.append('perturbed_image', pertFile);
    formData.append('amplification', amplification);

    const response = await axios.post(`${FASTAPI_URL}/robustness/difference-map`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });
    return response.data;
  },

  async profileRobustness(stegoFile, attackType = 'gaussian', params = {}, options = {}) {
    const formData = new FormData();
    formData.append('stego_image', stegoFile);
    if (options.coverFile) formData.append('cover_image', options.coverFile);
    formData.append('attack_type', attackType);

    if (params.std !== undefined) formData.append('std', params.std);
    if (params.mean !== undefined) formData.append('mean', params.mean);
    if (params.density !== undefined) formData.append('density', params.density);
    if (params.saltVsPepper !== undefined) formData.append('salt_vs_pepper', params.saltVsPepper);
    if (params.quality !== undefined) formData.append('quality', params.quality);
    if (params.kernelSize !== undefined) formData.append('kernel_size', params.kernelSize);
    if (params.sigma !== undefined) formData.append('sigma', params.sigma);
    if (params.seed !== undefined && params.seed !== null) formData.append('seed', params.seed);

    formData.append('extraction_method', options.extractionMethod || 'scatter');
    if (options.stegoKey) formData.append('stego_key', options.stegoKey);
    if (options.recipientPrivateKeyPem) formData.append('recipient_private_key_pem', options.recipientPrivateKeyPem);
    if (options.blockSize) formData.append('block_size', options.blockSize);
    if (options.originalPayload) formData.append('original_payload', options.originalPayload);

    const response = await axios.post(`${FASTAPI_URL}/robustness/profile`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async sweepRobustness(stegoFile, attackType = 'gaussian', intensities = '', options = {}) {
    const formData = new FormData();
    formData.append('stego_image', stegoFile);
    formData.append('attack_type', attackType);
    if (intensities) formData.append('intensities', intensities);

    formData.append('extraction_method', options.extractionMethod || 'scatter');
    if (options.stegoKey) formData.append('stego_key', options.stegoKey);
    if (options.recipientPrivateKeyPem) formData.append('recipient_private_key_pem', options.recipientPrivateKeyPem);
    if (options.blockSize) formData.append('block_size', options.blockSize);
    if (options.originalPayload) formData.append('original_payload', options.originalPayload);

    const response = await axios.post(`${FASTAPI_URL}/robustness/sweep`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Phase 20: Multi-Objective Genetic & Pareto Optimization
  async getOptimizationPresets() {
    const response = await axios.get(`${FASTAPI_URL}/optimize/presets`);
    return response.data;
  },

  async runGeneticOptimization(coverFile, message, profile = 'Balanced', generations = 4, populationSize = 8, stegoKey = 'GeneticOptimizerKey#2026') {
    const formData = new FormData();
    formData.append('cover_image', coverFile);
    formData.append('message', message);
    formData.append('profile', profile);
    formData.append('generations', generations);
    formData.append('population_size', populationSize);
    formData.append('stego_key', stegoKey);

    const response = await axios.post(`${FASTAPI_URL}/optimize/genetic`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async evaluateCustomChromosome(coverFile, message, chromosome = {}, profile = 'Balanced', stegoKey = 'GeneticOptimizerKey#2026') {
    const formData = new FormData();
    formData.append('cover_image', coverFile);
    formData.append('message', message);
    formData.append('profile', profile);
    if (chromosome.block_size !== undefined) formData.append('block_size', chromosome.block_size);
    if (chromosome.bits_high_texture !== undefined) formData.append('bits_high_texture', chromosome.bits_high_texture);
    if (chromosome.bits_medium !== undefined) formData.append('bits_medium', chromosome.bits_medium);
    if (chromosome.bits_smooth !== undefined) formData.append('bits_smooth', chromosome.bits_smooth);
    if (chromosome.decision_threshold !== undefined) formData.append('decision_threshold', chromosome.decision_threshold);
    if (chromosome.suitability_weight_high !== undefined) formData.append('suitability_weight_high', chromosome.suitability_weight_high);
    if (chromosome.suitability_weight_med !== undefined) formData.append('suitability_weight_med', chromosome.suitability_weight_med);
    formData.append('stego_key', stegoKey);

    const response = await axios.post(`${FASTAPI_URL}/optimize/evaluate`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

