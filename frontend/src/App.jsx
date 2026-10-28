import React, { useState, useEffect } from 'react';
import {
  Shield, Cpu, Lock, CheckCircle2, Server, Terminal, Sparkles,
  Upload, Download, Key, User, LogIn, UserPlus, LogOut, FileText,
  AlertTriangle, RefreshCw, Copy, Check, Eye, EyeOff, Activity, BarChart2, Award, Zap,
  Sliders, ShieldAlert, Target, TrendingUp, Compass
} from 'lucide-react';
import { authService } from './services/authService';
import { keyService } from './services/keyService';
import { operationService } from './services/operationService';
import { stegoService } from './services/stegoService';

export default function App() {
  const [activeTab, setActiveTab] = useState('pipeline'); // 'pipeline', 'encode', 'decode', 'ai-regions', 'steganalyzer', 'metrics', 'keys', 'dashboard', 'auth'

  // Service Health States
  const [fastApiStatus, setFastApiStatus] = useState('checking');
  const [aspNetStatus, setAspNetStatus] = useState('checking');

  // Auth States
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'
  const [authForm, setAuthForm] = useState({ username: '', email: '', password: '' });
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [showAuthPassword, setShowAuthPassword] = useState(false);

  // Key Vault States
  const [keyData, setKeyData] = useState(null);
  const [keyLoading, setKeyLoading] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const [vaultPrivateKey, setVaultPrivateKey] = useState('');
  const [showVaultPrivateKey, setShowVaultPrivateKey] = useState(false);
  const [copiedPrivateKey, setCopiedPrivateKey] = useState(false);

  // Encode States
  const [encodeMethod, setEncodeMethod] = useState('scatter'); // 'scatter', 'ai_adaptive', 'adaptive', 'baseline'
  const [encodeBlockSize, setEncodeBlockSize] = useState(16);
  const [encodeFile, setEncodeFile] = useState(null);
  const [encodePreview, setEncodePreview] = useState(null);
  const [encodeMessage, setEncodeMessage] = useState('');
  const [encodeStegoKey, setEncodeStegoKey] = useState('SecretStegoPassphrase#2026');
  const [showEncodeKey, setShowEncodeKey] = useState(false);
  const [encodeCapacity, setEncodeCapacity] = useState(null);
  const [encodeLoading, setEncodeLoading] = useState(false);
  const [encodeResult, setEncodeResult] = useState(null);
  const [encodeError, setEncodeError] = useState('');

  // Phase 17: Feedback Optimization States
  const [feedbackThreshold, setFeedbackThreshold] = useState(0.35);
  const [feedbackMaxIterations, setFeedbackMaxIterations] = useState(5);

  // Decode States
  const [decodeMethod, setDecodeMethod] = useState('scatter'); // 'feedback', 'scatter', 'ai_adaptive', 'adaptive', 'baseline'
  const [decodeBlockSize, setDecodeBlockSize] = useState(16);
  const [decodeFile, setDecodeFile] = useState(null);
  const [decodePreview, setDecodePreview] = useState(null);
  const [decodeStegoKey, setDecodeStegoKey] = useState('');
  const [showDecodeKey, setShowDecodeKey] = useState(false);
  const [decodeLoading, setDecodeLoading] = useState(false);
  const [decodeResult, setDecodeResult] = useState(null);
  const [decodeError, setDecodeError] = useState('');
  const [copiedDecoded, setCopiedDecoded] = useState(false);

  // Quality & Benchmark Metrics States (Phase 9)
  const [metricCoverFile, setMetricCoverFile] = useState(null);
  const [metricCoverPreview, setMetricCoverPreview] = useState(null);
  const [metricStegoFile, setMetricStegoFile] = useState(null);
  const [metricStegoPreview, setMetricStegoPreview] = useState(null);
  const [metricOrigText, setMetricOrigText] = useState('');
  const [metricRecovText, setMetricRecovText] = useState('');
  const [metricLoading, setMetricLoading] = useState(false);
  const [metricResult, setMetricResult] = useState(null);
  const [metricError, setMetricError] = useState('');
  const [metricsHistory, setMetricsHistory] = useState([]);

  // Phase 14 Direct 3-Way Empirical Comparison States (Baseline vs Rule vs AI)
  const [compCoverFile, setCompCoverFile] = useState(null);
  const [compCoverPreview, setCompCoverPreview] = useState(null);
  const [compMessage, setCompMessage] = useState('Final-Year B.Tech Research Project - AI-Selected Adaptive Steganography Test Payload 2026');
  const [compLoading, setCompLoading] = useState(false);
  const [compResult, setCompResult] = useState(null);
  const [compError, setCompError] = useState('');

  // Phase 13: AI Region Model Inspector States
  const [aiImageFile, setAiImageFile] = useState(null);
  const [aiImagePreview, setAiImagePreview] = useState(null);
  const [aiHeatmapUrl, setAiHeatmapUrl] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiHeatmapLoading, setAiHeatmapLoading] = useState(false);
  const [aiHeatmapError, setAiHeatmapError] = useState('');
  const [aiModelInfo, setAiModelInfo] = useState(null);
  const [aiViewMode, setAiViewMode] = useState('heatmap'); // 'heatmap' or 'original'

  // Phase 16: Deep Learning Steganalyzer CNN States
  const [detectFile, setDetectFile] = useState(null);
  const [detectPreview, setDetectPreview] = useState(null);
  const [detectThreshold, setDetectThreshold] = useState(0.35);
  const [detectLoading, setDetectLoading] = useState(false);
  const [detectResult, setDetectResult] = useState(null);
  const [detectError, setDetectError] = useState('');
  const [steganalyzerInfo, setSteganalyzerInfo] = useState(null);

  // Phase 18: One-Click End-to-End Orchestration Pipeline States
  const [pipelineCoverFile, setPipelineCoverFile] = useState(null);
  const [pipelineCoverPreview, setPipelineCoverPreview] = useState(null);
  const [pipelineMessage, setPipelineMessage] = useState('Confidential Research Payload: AI-Steganography System 2026');
  const [pipelineRecipientPubKey, setPipelineRecipientPubKey] = useState('');
  const [pipelineStegoKey, setPipelineStegoKey] = useState('');
  const [pipelineSecurityLevel, setPipelineSecurityLevel] = useState('Balanced'); // 'Quality', 'Balanced', 'Security'
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [pipelineResult, setPipelineResult] = useState(null);
  const [pipelineError, setPipelineError] = useState('');

  const [pipelineDecodeFile, setPipelineDecodeFile] = useState(null);
  const [pipelineDecodePreview, setPipelineDecodePreview] = useState(null);
  const [pipelinePrivateKeyPem, setPipelinePrivateKeyPem] = useState('');
  const [pipelineDecodeStegoKey, setPipelineDecodeStegoKey] = useState('');
  const [pipelineDecodeLoading, setPipelineDecodeLoading] = useState(false);
  const [pipelineDecodeResult, setPipelineDecodeResult] = useState(null);
  const [pipelineDecodeError, setPipelineDecodeError] = useState('');
  const [pipelineAuditHistory, setPipelineAuditHistory] = useState([]);
  const [copiedPipelineText, setCopiedPipelineText] = useState(false);

  // Phase 19: Robustness & Noise Perturbation Profiling States
  const [robustStegoFile, setRobustStegoFile] = useState(null);
  const [robustStegoPreview, setRobustStegoPreview] = useState(null);
  const [robustAttackType, setRobustAttackType] = useState('gaussian'); // 'gaussian', 'salt_pepper', 'jpeg', 'blur', 'speckle'
  const [robustStd, setRobustStd] = useState(2.0);
  const [robustDensity, setRobustDensity] = useState(0.01);
  const [robustJpegQuality, setRobustJpegQuality] = useState(85);
  const [robustBlurSigma, setRobustBlurSigma] = useState(1.0);
  const [robustSpeckleStd, setRobustSpeckleStd] = useState(0.05);
  const [robustExtractionMethod, setRobustExtractionMethod] = useState('scatter'); // 'scatter', 'ai_adaptive', 'adaptive', 'baseline', 'pipeline_hybrid', 'none'
  const [robustStegoKey, setRobustStegoKey] = useState('SecretStegoPassphrase#2026');
  const [robustPrivateKeyPem, setRobustPrivateKeyPem] = useState('');
  const [robustOrigPayload, setRobustOrigPayload] = useState('Confidential Research Payload: AI-Steganography System 2026');
  const [robustBlockSize, setRobustBlockSize] = useState(16);
  const [robustLoading, setRobustLoading] = useState(false);
  const [robustError, setRobustError] = useState('');
  const [robustPerturbedBlob, setRobustPerturbedBlob] = useState(null);
  const [robustPerturbedUrl, setRobustPerturbedUrl] = useState(null);
  const [robustDiffUrl, setRobustDiffUrl] = useState(null);
  const [robustProfileReport, setRobustProfileReport] = useState(null);
  const [robustSweepLoading, setRobustSweepLoading] = useState(false);
  const [robustSweepData, setRobustSweepData] = useState(null);
  const [robustSweepError, setRobustSweepError] = useState('');

  // Phase 20: Multi-Objective Genetic / Pareto Optimization States
  const [optCoverFile, setOptCoverFile] = useState(null);
  const [optCoverPreview, setOptCoverPreview] = useState(null);
  const [optMessage, setOptMessage] = useState('Final-Year B.Tech Research Project - Multi-Objective Evolutionary Steganography Optimization 2026');
  const [optProfile, setOptProfile] = useState('Balanced'); // 'Balanced', 'Quality', 'Security', 'Capacity'
  const [optGenerations, setOptGenerations] = useState(4);
  const [optPopulationSize, setOptPopulationSize] = useState(8);
  const [optStegoKey, setOptStegoKey] = useState('GeneticOptimizerKey#2026');
  const [optLoading, setOptLoading] = useState(false);
  const [optError, setOptError] = useState('');
  const [optResult, setOptResult] = useState(null);
  const [optAppliedAlert, setOptAppliedAlert] = useState(false);

  // Initial Load: Check services and load saved user
  useEffect(() => {
    checkServices();
    loadMetricsHistory();
    loadSteganalyzerInfo();
    const savedUser = authService.getCurrentUser();
    if (savedUser) {
      setUser(savedUser);
      loadUserKeys();
      loadOperationHistory();
    }
  }, []);

  const loadOperationHistory = async () => {
    try {
      const data = await operationService.getOperationHistory(20);
      setPipelineAuditHistory(data);
    } catch {
      // Ignore if offline
    }
  };

  const loadSteganalyzerInfo = async () => {
    try {
      const data = await stegoService.getSteganalyzerInfo();
      setSteganalyzerInfo(data);
    } catch {
      // Ignore if offline
    }
  };

  const checkServices = () => {
    // FastAPI
    fetch('http://127.0.0.1:8000/health')
      .then(res => res.json())
      .then(data => setFastApiStatus(data.status === 'healthy' ? 'healthy' : 'error'))
      .catch(() => setFastApiStatus('offline'));

    // ASP.NET Core
    fetch('http://localhost:5000/api/health')
      .then(res => res.json())
      .then(data => setAspNetStatus(data.status === 'healthy' ? 'healthy' : 'error'))
      .catch(() => setAspNetStatus('offline'));
  };

  const loadUserKeys = async () => {
    try {
      setKeyLoading(true);
      const data = await keyService.getMyPublicKey();
      setKeyData(data);
      if (data && data.publicKeyPem) {
        setPipelineRecipientPubKey(data.publicKeyPem);
      }
    } catch {
      setKeyData(null);
    } finally {
      setKeyLoading(false);
    }
  };

  // Auth Handlers
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);
    try {
      if (authMode === 'register') {
        const res = await authService.register(authForm.username, authForm.email, authForm.password);
        setUser(res);
      } else {
        const res = await authService.login(authForm.email, authForm.password);
        setUser(res);
      }
      loadUserKeys();
      loadOperationHistory();
      setAuthForm({ username: '', email: '', password: '' });
      setActiveTab('pipeline');
    } catch (err) {
      setAuthError(err.response?.data?.message || err.message || 'Authentication failed.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setKeyData(null);
  };

  const handleRegenerateKeys = async () => {
    setKeyLoading(true);
    try {
      const data = await keyService.regenerateKeys();
      setKeyData(data);
    } catch (err) {
      alert('Failed to regenerate keys: ' + (err.response?.data?.message || err.message));
    } finally {
      setKeyLoading(false);
    }
  };

  const handleTogglePrivateKey = async () => {
    if (showVaultPrivateKey) {
      setShowVaultPrivateKey(false);
      return;
    }
    if (!vaultPrivateKey) {
      try {
        const res = await keyService.getMyPrivateKey();
        if (res && res.privateKeyPem) {
          setVaultPrivateKey(res.privateKeyPem);
          setShowVaultPrivateKey(true);
        }
      } catch (err) {
        alert('Failed to retrieve private key: ' + (err.response?.data?.message || err.message));
      }
    } else {
      setShowVaultPrivateKey(true);
    }
  };

  // Phase 18: One-Click End-to-End Pipeline Handlers
  const handlePipelineCoverChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.type.includes('png')) {
      setPipelineError('Please select a lossless PNG image.');
      return;
    }
    setPipelineError('');
    setPipelineCoverFile(file);
    setPipelineResult(null);
    setPipelineCoverPreview(URL.createObjectURL(file));
  };

  const handlePipelineEncodeSubmit = async (e) => {
    e.preventDefault();
    if (!pipelineCoverFile || !pipelineMessage.trim()) return;
    if (!pipelineRecipientPubKey.trim()) {
      setPipelineError('Please provide a recipient RSA-4096 Public Key PEM.');
      return;
    }

    setPipelineLoading(true);
    setPipelineError('');
    try {
      const result = await stegoService.encodePipelineHybrid(
        pipelineCoverFile,
        pipelineMessage.trim(),
        pipelineRecipientPubKey.trim(),
        pipelineStegoKey.trim(),
        pipelineSecurityLevel,
        16
      );
      const downloadUrl = URL.createObjectURL(result.blob);
      setPipelineResult({ ...result, downloadUrl });

      // Automatically audit to ASP.NET Core DB if user is logged in
      if (user) {
        try {
          await operationService.recordOperation({
            operationType: 'Encode',
            coverImageHash: result.metadata.coverSha256,
            stegoImageHash: result.metadata.stegoSha256,
            payloadSizeBytes: result.metadata.rawPayloadBytes,
            securityLevel: result.metadata.securityLevel,
            detectabilityScore: result.metadata.finalPStego,
            psnrDb: result.metadata.psnr !== 'Infinity' ? parseFloat(result.metadata.psnr) : null,
            ssim: result.metadata.ssim,
            mse: result.metadata.mse,
            executionTimeMs: result.metadata.executionTimeMs,
          });
          loadOperationHistory();
        } catch {
          // Non-critical audit error
        }
      }
    } catch (err) {
      setPipelineError(err.response?.data?.detail || err.message || 'Pipeline orchestration failed.');
    } finally {
      setPipelineLoading(false);
    }
  };

  const handlePipelineDecodeImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setPipelineDecodeError('');
    setPipelineDecodeFile(file);
    setPipelineDecodeResult(null);
    setPipelineDecodePreview(URL.createObjectURL(file));
  };

  const handlePipelineDecodeSubmit = async (e) => {
    e.preventDefault();
    if (!pipelineDecodeFile || !pipelinePrivateKeyPem.trim()) {
      setPipelineDecodeError('Please provide both the stego image and recipient RSA Private Key.');
      return;
    }

    setPipelineDecodeLoading(true);
    setPipelineDecodeError('');
    try {
      const result = await stegoService.decodePipelineHybrid(
        pipelineDecodeFile,
        pipelinePrivateKeyPem.trim(),
        pipelineDecodeStegoKey.trim(),
        '',
        16
      );
      setPipelineDecodeResult(result);

      if (user) {
        try {
          await operationService.recordOperation({
            operationType: 'Decode',
            stegoImageHash: result.stego_sha256,
            payloadSizeBytes: result.payload_bytes,
            securityLevel: 'Authenticated',
            executionTimeMs: result.execution_time_ms,
          });
          loadOperationHistory();
        } catch {
          // Non-critical audit error
        }
      }
    } catch (err) {
      setPipelineDecodeError(err.response?.data?.detail || err.message || 'Pipeline extraction failed.');
    } finally {
      setPipelineDecodeLoading(false);
    }
  };

  // Encode Handlers
  const fetchCapacity = async (file, method = encodeMethod, bSize = encodeBlockSize) => {
    try {
      if (method === 'feedback' || method === 'scatter') {
        const cap = await stegoService.getScatterCapacity(file, bSize);
        setEncodeCapacity(cap);
      } else if (method === 'ai_adaptive') {
        const cap = await stegoService.getAiStegoCapacity(file, bSize);
        setEncodeCapacity(cap);
      } else if (method === 'adaptive') {
        const cap = await stegoService.getAdaptiveCapacity(file, bSize);
        setEncodeCapacity(cap);
      } else {
        const cap = await stegoService.getCapacity(file);
        setEncodeCapacity(cap);
      }
    } catch (err) {
      setEncodeError('Failed to calculate capacity: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCoverImageChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.includes('png')) {
      setEncodeError('Please select a lossless PNG image.');
      return;
    }

    setEncodeError('');
    setEncodeFile(file);
    setEncodeResult(null);
    setEncodePreview(URL.createObjectURL(file));

    await fetchCapacity(file, encodeMethod, encodeBlockSize);
  };

  const handleEncodeMethodChange = async (newMethod) => {
    setEncodeMethod(newMethod);
    setEncodeResult(null);
    if (encodeFile) {
      await fetchCapacity(encodeFile, newMethod, encodeBlockSize);
    }
  };

  const handleEncodeSubmit = async (e) => {
    e.preventDefault();
    if (!encodeFile || !encodeMessage.trim()) return;

    setEncodeLoading(true);
    setEncodeError('');
    try {
      let result;
      if (encodeMethod === 'feedback') {
        if (!encodeStegoKey.trim()) {
          setEncodeError('Please enter a secret steganographic key for feedback optimization.');
          setEncodeLoading(false);
          return;
        }
        result = await stegoService.encodeFeedbackMessage(
          encodeFile,
          encodeMessage,
          encodeStegoKey.trim(),
          encodeBlockSize,
          feedbackThreshold,
          feedbackMaxIterations
        );
      } else if (encodeMethod === 'scatter') {
        if (!encodeStegoKey.trim()) {
          setEncodeError('Please enter a secret steganographic key for PRNG block scattering.');
          setEncodeLoading(false);
          return;
        }
        result = await stegoService.encodeScatterMessage(encodeFile, encodeMessage, encodeStegoKey.trim(), encodeBlockSize);
      } else if (encodeMethod === 'ai_adaptive') {
        result = await stegoService.encodeAiMessage(encodeFile, encodeMessage, encodeBlockSize);
      } else if (encodeMethod === 'adaptive') {
        result = await stegoService.encodeAdaptiveMessage(encodeFile, encodeMessage, encodeBlockSize);
      } else {
        result = await stegoService.encodeMessage(encodeFile, encodeMessage);
      }
      const downloadUrl = URL.createObjectURL(result.blob);
      setEncodeResult({ ...result, downloadUrl });
    } catch (err) {
      setEncodeError(err.response?.data?.detail || err.message || 'Encoding failed.');
    } finally {
      setEncodeLoading(false);
    }
  };

  // Decode Handlers
  const handleDecodeImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setDecodeError('');
    setDecodeFile(file);
    setDecodeResult(null);
    setDecodePreview(URL.createObjectURL(file));
  };

  const handleDecodeSubmit = async (e) => {
    e.preventDefault();
    if (!decodeFile) return;

    setDecodeLoading(true);
    setDecodeError('');
    try {
      let result;
      if (decodeMethod === 'feedback') {
        if (!decodeStegoKey.trim()) {
          setDecodeError('Please provide the secret steganographic key used during feedback-optimized embedding.');
          setDecodeLoading(false);
          return;
        }
        result = await stegoService.decodeFeedbackMessage(decodeFile, decodeStegoKey.trim(), decodeBlockSize);
      } else if (decodeMethod === 'scatter') {
        if (!decodeStegoKey.trim()) {
          setDecodeError('Please provide the secret steganographic key to unshuffle and extract payload.');
          setDecodeLoading(false);
          return;
        }
        result = await stegoService.decodeScatterMessage(decodeFile, decodeStegoKey.trim(), decodeBlockSize);
      } else if (decodeMethod === 'ai_adaptive') {
        result = await stegoService.decodeAiMessage(decodeFile, decodeBlockSize);
      } else if (decodeMethod === 'adaptive') {
        result = await stegoService.decodeAdaptiveMessage(decodeFile, decodeBlockSize);
      } else {
        result = await stegoService.decodeMessage(decodeFile);
      }
      setDecodeResult(result);
    } catch (err) {
      setDecodeError(err.response?.data?.detail || err.message || 'Failed to extract payload.');
    } finally {
      setDecodeLoading(false);
    }
  };

  // Phase 14 Direct 3-Way Comparison Handlers
  const handleCompCoverChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setCompError('');
    setCompCoverFile(file);
    setCompResult(null);
    setCompCoverPreview(URL.createObjectURL(file));
  };

  const handleCompSubmit = async (e) => {
    e.preventDefault();
    if (!compCoverFile || !compMessage.trim()) {
      setCompError('Please select a Cover PNG and enter a test secret message.');
      return;
    }
    setCompLoading(true);
    setCompError('');
    try {
      const res = await stegoService.compareAllThreeMethods(compCoverFile, compMessage, 16);
      setCompResult(res);
    } catch (err) {
      setCompError(err.response?.data?.detail || err.message || 'Comparative benchmark failed.');
    } finally {
      setCompLoading(false);
    }
  };

  // Phase 13: AI Region Model Handlers
  const handleAiImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setAiHeatmapError('');
    setAiImageFile(file);
    setAiAnalysis(null);
    setAiHeatmapUrl(null);
    setAiImagePreview(URL.createObjectURL(file));
  };

  const handleAiAnalyzeSubmit = async (e) => {
    e.preventDefault();
    if (!aiImageFile) return;

    setAiHeatmapLoading(true);
    setAiHeatmapError('');
    try {
      const [analysisData, heatmapRes, info] = await Promise.all([
        stegoService.analyzeImageRegions(aiImageFile, 16),
        stegoService.getAiRegionHeatmap(aiImageFile, 16, 0.45),
        aiModelInfo ? Promise.resolve(aiModelInfo) : stegoService.getAiRegionInfo(),
      ]);

      setAiAnalysis(analysisData);
      setAiHeatmapUrl(URL.createObjectURL(heatmapRes.blob));
      setAiModelInfo(info);
    } catch (err) {
      setAiHeatmapError(err.response?.data?.detail || err.message || 'AI Region analysis failed.');
    } finally {
      setAiHeatmapLoading(false);
    }
  };

  // Phase 16: CNN Steganalyzer Handlers
  const handleDetectFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setDetectError('');
    setDetectFile(file);
    setDetectResult(null);
    setDetectPreview(URL.createObjectURL(file));
  };

  const handleDetectSubmit = async (e) => {
    e.preventDefault();
    if (!detectFile) return;

    setDetectLoading(true);
    setDetectError('');
    try {
      const [res, info] = await Promise.all([
        stegoService.detectStego(detectFile, detectThreshold),
        steganalyzerInfo ? Promise.resolve(steganalyzerInfo) : stegoService.getSteganalyzerInfo(),
      ]);
      setDetectResult(res);
      if (!steganalyzerInfo) setSteganalyzerInfo(info);
    } catch (err) {
      setDetectError(err.response?.data?.detail || err.message || 'Steganalysis detection failed.');
    } finally {
      setDetectLoading(false);
    }
  };

  // Metrics Handlers (Phase 9)
  const loadMetricsHistory = async () => {
    try {
      const data = await stegoService.getMetricsHistory();
      setMetricsHistory(Array.isArray(data) ? data : []);
    } catch {
      setMetricsHistory([]);
    }
  };

  const handleMetricCoverChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setMetricError('');
    setMetricCoverFile(file);
    setMetricCoverPreview(URL.createObjectURL(file));
  };

  const handleMetricStegoChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setMetricError('');
    setMetricStegoFile(file);
    setMetricStegoPreview(URL.createObjectURL(file));
  };

  const handleCompareMetricsSubmit = async (e) => {
    e.preventDefault();
    if (!metricCoverFile || !metricStegoFile) {
      setMetricError('Please provide both Cover PNG and Stego PNG images to run quality evaluation.');
      return;
    }

    setMetricLoading(true);
    setMetricError('');
    try {
      const res = await stegoService.compareMetrics(
        metricCoverFile,
        metricStegoFile,
        metricOrigText || null,
        metricRecovText || null,
        'Baseline_LSB'
      );
      setMetricResult(res);
      loadMetricsHistory();
    } catch (err) {
      setMetricError(err.response?.data?.detail || err.message || 'Quality metrics calculation failed.');
    } finally {
      setMetricLoading(false);
    }
  };

  // Phase 19: Robustness Lab Handlers
  const handleRobustFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setRobustError('');
    setRobustStegoFile(file);
    setRobustProfileReport(null);
    setRobustPerturbedBlob(null);
    setRobustPerturbedUrl(null);
    setRobustDiffUrl(null);
    setRobustSweepData(null);
    setRobustStegoPreview(URL.createObjectURL(file));
  };

  const handleUseLastPipelineStego = () => {
    if (pipelineResult?.blob) {
      const file = new File([pipelineResult.blob], 'pipeline_stego.png', { type: 'image/png' });
      setRobustError('');
      setRobustStegoFile(file);
      setRobustProfileReport(null);
      setRobustPerturbedBlob(null);
      setRobustPerturbedUrl(null);
      setRobustDiffUrl(null);
      setRobustSweepData(null);
      setRobustStegoPreview(URL.createObjectURL(pipelineResult.blob));
      setRobustExtractionMethod('pipeline_hybrid');
      if (vaultPrivateKey) setRobustPrivateKeyPem(vaultPrivateKey);
    } else if (encodeResult?.blob) {
      const file = new File([encodeResult.blob], 'encoded_stego.png', { type: 'image/png' });
      setRobustError('');
      setRobustStegoFile(file);
      setRobustProfileReport(null);
      setRobustPerturbedBlob(null);
      setRobustPerturbedUrl(null);
      setRobustDiffUrl(null);
      setRobustSweepData(null);
      setRobustStegoPreview(URL.createObjectURL(encodeResult.blob));
      setRobustExtractionMethod(encodeMethod);
      setRobustStegoKey(encodeStegoKey);
    }
  };

  const getAttackParams = () => {
    switch (robustAttackType) {
      case 'gaussian':
        return { std: parseFloat(robustStd), mean: 0.0 };
      case 'salt_pepper':
        return { density: parseFloat(robustDensity), saltVsPepper: 0.5 };
      case 'jpeg':
        return { quality: parseInt(robustJpegQuality, 10) };
      case 'blur':
        return { kernelSize: 3, sigma: parseFloat(robustBlurSigma) };
      case 'speckle':
        return { std: parseFloat(robustSpeckleStd) };
      default:
        return { std: 2.0 };
    }
  };

  const handleRunAttackAndProfile = async (e) => {
    if (e) e.preventDefault();
    if (!robustStegoFile) {
      setRobustError('Please upload or select a stego image to test.');
      return;
    }

    setRobustLoading(true);
    setRobustError('');
    setRobustProfileReport(null);
    setRobustPerturbedBlob(null);
    setRobustPerturbedUrl(null);
    setRobustDiffUrl(null);

    const params = getAttackParams();
    const options = {
      extractionMethod: robustExtractionMethod,
      stegoKey: robustStegoKey,
      recipientPrivateKeyPem: robustPrivateKeyPem,
      blockSize: robustBlockSize,
      originalPayload: robustOrigPayload || undefined,
    };

    try {
      // 1. Profile attack & tamper detection
      const report = await stegoService.profileRobustness(robustStegoFile, robustAttackType, params, options);
      setRobustProfileReport(report);

      // 2. Generate perturbed visual PNG
      const pertRes = await stegoService.perturbImage(robustStegoFile, robustAttackType, params);
      setRobustPerturbedBlob(pertRes.blob);
      const pertUrl = URL.createObjectURL(pertRes.blob);
      setRobustPerturbedUrl(pertUrl);

      // 3. Generate high-contrast residual difference map
      const pertFile = new File([pertRes.blob], 'perturbed.png', { type: 'image/png' });
      const diffBlob = await stegoService.getDifferenceMap(robustStegoFile, pertFile, 15.0);
      setRobustDiffUrl(URL.createObjectURL(diffBlob));
    } catch (err) {
      setRobustError(err.response?.data?.detail || err.message || 'Robustness profiling failed.');
    } finally {
      setRobustLoading(false);
    }
  };

  const handleRunSweep = async () => {
    if (!robustStegoFile) {
      setRobustSweepError('Please upload or select a stego image first.');
      return;
    }

    setRobustSweepLoading(true);
    setRobustSweepError('');
    setRobustSweepData(null);

    const options = {
      extractionMethod: robustExtractionMethod,
      stegoKey: robustStegoKey,
      recipientPrivateKeyPem: robustPrivateKeyPem,
      blockSize: robustBlockSize,
      originalPayload: robustOrigPayload || undefined,
    };

    try {
      const sweepRes = await stegoService.sweepRobustness(robustStegoFile, robustAttackType, '', options);
      setRobustSweepData(sweepRes.sweep_results);
    } catch (err) {
      setRobustSweepError(err.response?.data?.detail || err.message || 'Parameter degradation sweep failed.');
    } finally {
      setRobustSweepLoading(false);
    }
  };

  const handleDownloadPerturbed = () => {
    if (!robustPerturbedBlob) return;
    const url = URL.createObjectURL(robustPerturbedBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `perturbed_${robustAttackType}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // Phase 20: Pareto & Genetic Optimization Handlers
  const handleOptCoverChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setOptError('');
    setOptCoverFile(file);
    setOptResult(null);
    setOptCoverPreview(URL.createObjectURL(file));
  };

  const handleRunGeneticOptimization = async (e) => {
    if (e) e.preventDefault();
    if (!optCoverFile || !optMessage.trim()) {
      setOptError('Please select a Cover PNG image and enter a test payload.');
      return;
    }

    setOptLoading(true);
    setOptError('');
    setOptResult(null);

    try {
      const res = await stegoService.runGeneticOptimization(
        optCoverFile,
        optMessage,
        optProfile,
        optGenerations,
        optPopulationSize,
        optStegoKey
      );
      setOptResult(res);
    } catch (err) {
      setOptError(err.response?.data?.detail || err.message || 'Genetic optimization failed.');
    } finally {
      setOptLoading(false);
    }
  };

  const handleApplyOptimizedToEmbed = () => {
    if (!optResult?.best_evaluation?.chromosome) return;
    const bestCh = optResult.best_evaluation.chromosome;

    setEncodeMethod('scatter');
    setEncodeBlockSize(bestCh.block_size);
    setEncodeStegoKey(optStegoKey);
    setEncodeMessage(optMessage);
    if (optCoverFile) {
      setEncodeFile(optCoverFile);
      setEncodePreview(optCoverPreview);
    }
    setOptAppliedAlert(true);
    setTimeout(() => {
      setOptAppliedAlert(false);
      setActiveTab('encode');
    }, 1200);
  };

  const messageSizeBytes = new Blob([encodeMessage]).size;
  const isOversized = encodeCapacity && messageSizeBytes > encodeCapacity.max_payload_bytes;
  const capacityPercent = encodeCapacity
    ? Math.min(100, ((messageSizeBytes / encodeCapacity.max_payload_bytes) * 100).toFixed(1))
    : 0;

  return (
    <div style={{ maxWidth: '1320px', margin: '0 auto', padding: '24px 20px', minHeight: '100vh' }}>
      {/* Top Header Row */}
      <header className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', marginBottom: '16px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'var(--gradient-cyber)', padding: '10px', borderRadius: '10px', color: '#fff', display: 'flex' }}>
            <Shield size={24} />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: '800', letterSpacing: '-0.02em' }}>
              Adaptive Steganography <span className="gradient-text">AI</span>
            </h2>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Final-Year B.Tech Research Platform</span>
          </div>
        </div>

        {/* Right Status Badges & Dedicated User Sign In Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: '600', padding: '5px 10px', borderRadius: '999px', background: fastApiStatus === 'healthy' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: fastApiStatus === 'healthy' ? '#10b981' : '#f43f5e' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: fastApiStatus === 'healthy' ? '#10b981' : '#f43f5e' }}></span>
              FastAPI: {fastApiStatus}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: '600', padding: '5px 10px', borderRadius: '999px', background: aspNetStatus === 'healthy' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: aspNetStatus === 'healthy' ? '#10b981' : '#f43f5e' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: aspNetStatus === 'healthy' ? '#10b981' : '#f43f5e' }}></span>
              C# API: {aspNetStatus}
            </span>
          </div>

          <button
            onClick={() => setActiveTab('auth')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: '600',
              color: '#fff',
              background: activeTab === 'auth' ? 'var(--gradient-cyber)' : 'rgba(255, 255, 255, 0.08)',
              border: activeTab === 'auth' ? '1px solid transparent' : '1px solid var(--border-color)',
              transition: 'all 0.2s ease',
            }}
          >
            <User size={15} color={activeTab === 'auth' ? '#fff' : '#06b6d4'} />
            {user ? user.username : 'Sign In'}
          </button>
        </div>
      </header>

      {/* Secondary Workspace Navigation Strip */}
      <nav className="glass-panel" style={{ padding: '6px', marginBottom: '28px', display: 'flex', gap: '6px', flexWrap: 'wrap', justifyContent: 'center' }}>
        {[
          { id: 'pipeline', label: 'One-Click Studio', icon: Zap },
          { id: 'encode', label: 'Embed (Encode)', icon: Lock },
          { id: 'decode', label: 'Extract (Decode)', icon: FileText },
          { id: 'robustness', label: 'Robustness Lab', icon: AlertTriangle },
          { id: 'optimizer', label: 'Pareto Optimizer', icon: Target },
          { id: 'ai-regions', label: 'AI Region Heatmap', icon: Sparkles },
          { id: 'steganalyzer', label: 'CNN Steganalyzer', icon: Eye },
          { id: 'metrics', label: 'Quality & Benchmarks', icon: Activity },
          { id: 'keys', label: 'RSA Key Vault', icon: Key },
          { id: 'dashboard', label: 'Architecture', icon: Cpu },
        ].map(tab => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: '600',
                color: active ? '#fff' : 'var(--text-secondary)',
                background: active ? 'var(--gradient-cyber)' : 'transparent',
                transition: 'all 0.2s ease',
                flexGrow: 1,
                justifyContent: 'center',
                minWidth: '125px',
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* TAB 0: ONE-CLICK END-TO-END PIPELINE STUDIO (PHASE 18) */}
      {activeTab === 'pipeline' && (
        <div>
          {/* Studio Header */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: '800', color: '#ec4899', background: 'rgba(236, 72, 153, 0.15)', padding: '4px 10px', borderRadius: '999px', letterSpacing: '0.5px' }}>
                <Zap size={13} /> PHASE 18 UNIFIED ARCHITECTURE
              </span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Multi-Tier Defense-in-Depth Pipeline
              </span>
            </div>
            <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              One-Click End-to-End Stego Orchestration Studio
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '1000px' }}>
              Seamlessly integrates all research layers into a single atomic workflow: RSA-4096-OAEP key encapsulation, AES-256-GCM authenticated payload encryption, Random Forest region selection, PRNG key block scattering, SRM-CNN closed-loop feedback optimization, and SQL Server forensic auditing.
            </p>
          </div>

          {/* Architecture Pipeline Stepper / Badges */}
          <div className="glass-panel" style={{ padding: '14px 18px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', marginRight: '4px' }}>ACTIVE PIPELINE:</span>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#a855f7', background: 'rgba(168, 85, 247, 0.12)', padding: '3px 8px', borderRadius: '6px' }}>1. RSA-4096-OAEP</span>
              <span style={{ color: 'var(--text-muted)' }}>→</span>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#06b6d4', background: 'rgba(6, 182, 212, 0.12)', padding: '3px 8px', borderRadius: '6px' }}>2. AES-256-GCM</span>
              <span style={{ color: 'var(--text-muted)' }}>→</span>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.12)', padding: '3px 8px', borderRadius: '6px' }}>3. RF Classifier</span>
              <span style={{ color: 'var(--text-muted)' }}>→</span>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#c084fc', background: 'rgba(192, 132, 252, 0.12)', padding: '3px 8px', borderRadius: '6px' }}>4. PRNG Scatter</span>
              <span style={{ color: 'var(--text-muted)' }}>→</span>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#ec4899', background: 'rgba(236, 72, 153, 0.12)', padding: '3px 8px', borderRadius: '6px' }}>5. SRM-CNN Loop</span>
              <span style={{ color: 'var(--text-muted)' }}>→</span>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '3px 8px', borderRadius: '6px' }}>6. LocalDB Audit</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '11px', color: keyData ? '#10b981' : '#f59e0b', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Key size={12} /> {keyData ? `Vault Key: ${keyData.keyFingerprint?.slice(0, 16)}...` : 'Vault Key: Not Signed In'}
              </span>
            </div>
          </div>

          {/* Two-Column Grid: Left = Encrypt & Embed, Right = Extract & Decrypt */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: '24px', marginBottom: '24px' }}>
            {/* COLUMN 1: ONE-CLICK ENCRYPT & EMBED */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#ec4899' }}>
                <Lock size={18} /> 1. End-to-End Encrypt & Embed
              </h2>

              {/* Cover Image Upload */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Cover Image (Lossless PNG)
                </label>
                <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '10px', padding: '20px', textAlign: 'center', cursor: 'pointer', background: 'rgba(0,0,0,0.15)' }}>
                  <Upload size={24} color="var(--text-muted)" style={{ margin: '0 auto 8px' }} />
                  <span style={{ display: 'block', fontSize: '13px', fontWeight: '600' }}>
                    {pipelineCoverFile ? pipelineCoverFile.name : 'Select Cover PNG Image'}
                  </span>
                  <input type="file" accept="image/png" onChange={handlePipelineCoverChange} style={{ display: 'none' }} />
                </label>
                {pipelineCoverPreview && (
                  <div style={{ marginTop: '10px', textAlign: 'center' }}>
                    <img src={pipelineCoverPreview} alt="Cover Preview" style={{ maxHeight: '140px', borderRadius: '6px', border: '1px solid var(--border-color)' }} />
                  </div>
                )}
              </div>

              {/* Recipient RSA-4096 Public Key PEM */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)' }}>
                    Recipient RSA-4096 Public Key PEM
                  </label>
                  {keyData && (
                    <button
                      type="button"
                      onClick={() => setPipelineRecipientPubKey(keyData.publicKeyPem)}
                      style={{ background: 'none', border: 'none', color: '#06b6d4', fontSize: '11px', cursor: 'pointer', textDecoration: 'underline' }}
                    >
                      Use My Vault Key
                    </button>
                  )}
                </div>
                <textarea
                  rows={3}
                  value={pipelineRecipientPubKey}
                  onChange={(e) => setPipelineRecipientPubKey(e.target.value)}
                  placeholder="Paste recipient's -----BEGIN PUBLIC KEY----- PEM..."
                  style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '8px', color: '#a855f7', fontFamily: 'var(--font-mono)', fontSize: '11px', resize: 'vertical' }}
                />
              </div>

              {/* Secret Message Input */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Secret Message Payload
                </label>
                <textarea
                  rows={3}
                  value={pipelineMessage}
                  onChange={(e) => setPipelineMessage(e.target.value)}
                  placeholder="Enter confidential secret message..."
                  style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '10px', color: '#fff', fontSize: '13px', resize: 'vertical' }}
                />
              </div>

              {/* Security Profile Selection */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Security & Anti-Steganalysis Profile
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                  {[
                    { id: 'Balanced', label: 'Balanced', sub: 'τ=0.35, k≤5' },
                    { id: 'Quality', label: 'High Fidelity', sub: 'τ=0.45, k≤3' },
                    { id: 'Security', label: 'Max Stealth', sub: 'τ=0.25, k≤7' },
                  ].map(p => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setPipelineSecurityLevel(p.id)}
                      style={{
                        padding: '8px',
                        borderRadius: '6px',
                        border: pipelineSecurityLevel === p.id ? '1px solid #ec4899' : '1px solid var(--border-color)',
                        background: pipelineSecurityLevel === p.id ? 'rgba(236, 72, 153, 0.15)' : 'rgba(0,0,0,0.2)',
                        color: pipelineSecurityLevel === p.id ? '#f472b6' : 'var(--text-secondary)',
                        fontSize: '11px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        textAlign: 'center',
                      }}
                    >
                      <div>{p.label}</div>
                      <span style={{ fontSize: '9px', opacity: 0.75 }}>{p.sub}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Stego Passphrase */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  Stego Seed Key (Optional, auto-derived from key fingerprint if blank)
                </label>
                <input
                  type="text"
                  value={pipelineStegoKey}
                  onChange={(e) => setPipelineStegoKey(e.target.value)}
                  placeholder="Auto-derived from recipient fingerprint..."
                  style={{ width: '100%', padding: '8px 10px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontSize: '12px' }}
                />
              </div>

              {pipelineError && (
                <div style={{ padding: '10px 12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '6px', color: '#f43f5e', fontSize: '12px', marginBottom: '14px' }}>
                  {pipelineError}
                </div>
              )}

              <button
                onClick={handlePipelineEncodeSubmit}
                disabled={!pipelineCoverFile || !pipelineMessage.trim() || !pipelineRecipientPubKey.trim() || pipelineLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  background: !pipelineCoverFile || !pipelineMessage.trim() || !pipelineRecipientPubKey.trim() ? 'rgba(255,255,255,0.1)' : 'var(--gradient-cyber)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '14px',
                  cursor: !pipelineCoverFile ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {pipelineLoading ? <RefreshCw className="animate-spin" size={16} /> : <Zap size={16} />}
                {pipelineLoading ? 'Executing Hybrid Stego Pipeline...' : 'Run One-Click Orchestration'}
              </button>

              {/* Output & Forensic Certificate */}
              {pipelineResult && (
                <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: '700', color: '#10b981', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={14} /> Pipeline Completed Successfully
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Execution: {pipelineResult.metadata.executionTimeMs} ms
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginBottom: '12px' }}>
                    <div style={{ padding: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>PSNR Fidelity</span>
                      <p style={{ fontSize: '13px', fontWeight: '700', color: '#38bdf8' }}>{pipelineResult.metadata.psnr} dB</p>
                    </div>
                    <div style={{ padding: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>SSIM Score</span>
                      <p style={{ fontSize: '13px', fontWeight: '700', color: '#a855f7' }}>{pipelineResult.metadata.ssim}</p>
                    </div>
                    <div style={{ padding: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Final P(stego)</span>
                      <p style={{ fontSize: '13px', fontWeight: '700', color: pipelineResult.metadata.finalPStego < 0.35 ? '#10b981' : '#f59e0b' }}>
                        {pipelineResult.metadata.finalPStego}
                      </p>
                    </div>
                    <div style={{ padding: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Feedback Status</span>
                      <p style={{ fontSize: '13px', fontWeight: '700', color: '#ec4899' }}>
                        {pipelineResult.metadata.converged ? 'Converged' : 'Minimized'} ({pipelineResult.metadata.iterationsRun} iters)
                      </p>
                    </div>
                  </div>

                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '12px', wordBreak: 'break-all' }}>
                    <div>Cover SHA-256: <code>{pipelineResult.metadata.coverSha256}</code></div>
                    <div>Stego SHA-256: <code>{pipelineResult.metadata.stegoSha256}</code></div>
                  </div>

                  <a
                    href={pipelineResult.downloadUrl}
                    download="stego_hybrid_orchestrated.png"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      width: '100%',
                      padding: '10px',
                      background: 'rgba(16, 185, 129, 0.15)',
                      border: '1px solid #10b981',
                      borderRadius: '6px',
                      color: '#10b981',
                      fontWeight: '700',
                      fontSize: '13px',
                      textDecoration: 'none',
                    }}
                  >
                    <Download size={15} /> Download Lossless Stego PNG
                  </a>
                </div>
              )}
            </div>

            {/* COLUMN 2: ONE-CLICK EXTRACT & DECRYPT */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#06b6d4' }}>
                <CheckCircle2 size={18} /> 2. End-to-End Extract & Decrypt
              </h2>

              {/* Stego Image Upload */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Stego Image (PNG)
                </label>
                <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '10px', padding: '20px', textAlign: 'center', cursor: 'pointer', background: 'rgba(0,0,0,0.15)' }}>
                  <Upload size={24} color="var(--text-muted)" style={{ margin: '0 auto 8px' }} />
                  <span style={{ display: 'block', fontSize: '13px', fontWeight: '600' }}>
                    {pipelineDecodeFile ? pipelineDecodeFile.name : 'Select Stego PNG Image'}
                  </span>
                  <input type="file" accept="image/png" onChange={handlePipelineDecodeImageChange} style={{ display: 'none' }} />
                </label>
                {pipelineDecodePreview && (
                  <div style={{ marginTop: '10px', textAlign: 'center' }}>
                    <img src={pipelineDecodePreview} alt="Stego Preview" style={{ maxHeight: '140px', borderRadius: '6px', border: '1px solid var(--border-color)' }} />
                  </div>
                )}
              </div>

              {/* Recipient Private Key PEM */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)' }}>
                    Recipient RSA-4096 Private Key PEM (Required for Envelope Decapsulation)
                  </label>
                  {user && (
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          const res = await keyService.getMyPrivateKey();
                          if (res && res.privateKeyPem) {
                            setPipelinePrivateKeyPem(res.privateKeyPem);
                          }
                        } catch (err) {
                          alert('Failed to retrieve private key: ' + (err.response?.data?.message || err.message));
                        }
                      }}
                      style={{ background: 'none', border: 'none', color: '#f43f5e', fontSize: '11px', cursor: 'pointer', textDecoration: 'underline' }}
                    >
                      Use My Vault Private Key
                    </button>
                  )}
                </div>
                <textarea
                  rows={4}
                  value={pipelinePrivateKeyPem}
                  onChange={(e) => setPipelinePrivateKeyPem(e.target.value)}
                  placeholder="Paste recipient's -----BEGIN RSA PRIVATE KEY----- or -----BEGIN PRIVATE KEY----- PEM..."
                  style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '8px', color: '#f43f5e', fontFamily: 'var(--font-mono)', fontSize: '11px', resize: 'vertical' }}
                />
              </div>

              {/* Optional Stego Passphrase */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  Stego Passphrase (Optional, leave blank if auto-derived from key)
                </label>
                <input
                  type="text"
                  value={pipelineDecodeStegoKey}
                  onChange={(e) => setPipelineDecodeStegoKey(e.target.value)}
                  placeholder="Optional stego passphrase..."
                  style={{ width: '100%', padding: '8px 10px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontSize: '12px' }}
                />
              </div>

              {pipelineDecodeError && (
                <div style={{ padding: '10px 12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '6px', color: '#f43f5e', fontSize: '12px', marginBottom: '14px' }}>
                  {pipelineDecodeError}
                </div>
              )}

              <button
                onClick={handlePipelineDecodeSubmit}
                disabled={!pipelineDecodeFile || !pipelinePrivateKeyPem.trim() || pipelineDecodeLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  background: !pipelineDecodeFile || !pipelinePrivateKeyPem.trim() ? 'rgba(255,255,255,0.1)' : 'var(--gradient-cyber)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '14px',
                  cursor: !pipelineDecodeFile ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {pipelineDecodeLoading ? <RefreshCw className="animate-spin" size={16} /> : <FileText size={16} />}
                {pipelineDecodeLoading ? 'Extracting & Decrypting...' : 'Extract & Authenticate Payload'}
              </button>

              {/* Decrypted Payload Result */}
              {pipelineDecodeResult && (
                <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(6, 182, 212, 0.3)', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '11px', fontWeight: '700', color: '#10b981', background: 'rgba(16, 185, 129, 0.15)', padding: '3px 8px', borderRadius: '999px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle2 size={12} /> AES-GCM Authenticated
                      </span>
                      <span style={{ fontSize: '11px', fontWeight: '700', color: '#ec4899', background: 'rgba(236, 72, 153, 0.15)', padding: '3px 8px', borderRadius: '999px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <RefreshCw size={11} /> Sync Iteration: k={pipelineDecodeResult.opt_iteration}
                      </span>
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {pipelineDecodeResult.execution_time_ms} ms
                    </span>
                  </div>

                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Decrypted Plaintext Secret:
                  </label>
                  <div style={{ position: 'relative', marginBottom: '8px' }}>
                    <textarea
                      readOnly
                      rows={4}
                      value={pipelineDecodeResult.payload_text || '(Binary Data)'}
                      style={{
                        width: '100%',
                        background: 'rgba(0,0,0,0.4)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        padding: '10px 36px 10px 10px',
                        color: '#06b6d4',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '13px',
                      }}
                    />
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(pipelineDecodeResult.payload_text || '');
                        setCopiedPipelineText(true);
                        setTimeout(() => setCopiedPipelineText(false), 2000);
                      }}
                      style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        padding: '4px 8px',
                        background: 'rgba(255,255,255,0.1)',
                        border: 'none',
                        borderRadius: '4px',
                        color: '#fff',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '11px',
                      }}
                    >
                      {copiedPipelineText ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                      {copiedPipelineText ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Section 3: Forensic Audit & Operations History (LocalDB) */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Server size={18} color="#06b6d4" /> SQL Server Forensic Audit Trail (LocalDB)
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Immutable audit records for all steganographic operations executed by authenticated users.
                </p>
              </div>
              <button
                type="button"
                onClick={loadOperationHistory}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  color: 'var(--text-secondary)',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                <RefreshCw size={13} /> Refresh Audit Logs
              </button>
            </div>

            {pipelineAuditHistory && pipelineAuditHistory.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '8px' }}>Timestamp</th>
                      <th style={{ padding: '8px' }}>Type</th>
                      <th style={{ padding: '8px' }}>Profile</th>
                      <th style={{ padding: '8px' }}>Payload</th>
                      <th style={{ padding: '8px' }}>PSNR (dB)</th>
                      <th style={{ padding: '8px' }}>SSIM</th>
                      <th style={{ padding: '8px' }}>P(stego)</th>
                      <th style={{ padding: '8px' }}>Exec Time</th>
                      <th style={{ padding: '8px' }}>Stego SHA-256</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pipelineAuditHistory.map((op) => (
                      <tr key={op.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>
                          {new Date(op.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </td>
                        <td style={{ padding: '8px' }}>
                          <span style={{ fontSize: '10px', fontWeight: '700', padding: '2px 6px', borderRadius: '4px', background: op.operationType === 'Encode' ? 'rgba(236, 72, 153, 0.15)' : 'rgba(6, 182, 212, 0.15)', color: op.operationType === 'Encode' ? '#f472b6' : '#06b6d4' }}>
                            {op.operationType}
                          </span>
                        </td>
                        <td style={{ padding: '8px', color: 'var(--text-muted)' }}>{op.securityLevel || 'Balanced'}</td>
                        <td style={{ padding: '8px' }}>{op.payloadSizeBytes} B</td>
                        <td style={{ padding: '8px', color: '#38bdf8' }}>{op.psnrDb ? `${op.psnrDb} dB` : '-'}</td>
                        <td style={{ padding: '8px', color: '#a855f7' }}>{op.ssim || '-'}</td>
                        <td style={{ padding: '8px', color: op.detectabilityScore !== null ? (op.detectabilityScore < 0.35 ? '#10b981' : '#f59e0b') : 'var(--text-muted)' }}>
                          {op.detectabilityScore !== null ? op.detectabilityScore : '-'}
                        </td>
                        <td style={{ padding: '8px', color: 'var(--text-muted)' }}>{op.executionTimeMs} ms</td>
                        <td style={{ padding: '8px', fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)' }}>
                          {op.stegoImageHash ? `${op.stegoImageHash.slice(0, 12)}...` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '28px', color: 'var(--text-muted)', fontSize: '13px' }}>
                <p>No audit records found. Sign in and execute an end-to-end operation to populate the SQL Server forensic trail.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 1: ENCODE WORKSPACE */}
      {activeTab === 'encode' && (
        <div>
          <div style={{ marginBottom: '24px' }}>
            <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              Steganographic Embedding Workspace
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
              Upload a clean cover PNG, compose your secret message, and embed it with verified LSB steganography.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px' }}>
            {/* Input Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Upload size={18} color="#06b6d4" /> 1. Select Cover Image (PNG)
              </h3>

              <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '12px', padding: '32px 20px', textAlign: 'center', cursor: 'pointer', marginBottom: '20px', background: 'rgba(0,0,0,0.15)' }}>
                <Upload size={32} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
                <span style={{ display: 'block', fontSize: '14px', fontWeight: '600' }}>
                  {encodeFile ? encodeFile.name : 'Click or Drag & Drop Cover Image'}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Only lossless PNG images supported</span>
                <input type="file" accept="image/png" onChange={handleCoverImageChange} style={{ display: 'none' }} />
              </label>

              {encodePreview && (
                <div style={{ marginBottom: '20px', textAlign: 'center' }}>
                  <img src={encodePreview} alt="Cover Preview" style={{ maxHeight: '180px', borderRadius: '8px', border: '1px solid var(--border-color)' }} />
                  {encodeCapacity && (
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginTop: '10px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                      <span>Resolution: {encodeCapacity.width} × {encodeCapacity.height}</span>
                      <span>Max Capacity: {encodeCapacity.max_payload_bytes.toLocaleString()} Bytes</span>
                    </div>
                  )}
                </div>
              )}

              {/* Steganography Algorithm Selection */}
              <div style={{ marginBottom: '20px' }}>
                <span style={{ display: 'block', fontSize: '13px', fontWeight: '700', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                  2. Select Steganographic Strategy
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => handleEncodeMethodChange('feedback')}
                    style={{
                      padding: '10px 10px',
                      borderRadius: '8px',
                      border: encodeMethod === 'feedback' ? '1px solid #ec4899' : '1px solid var(--border-color)',
                      background: encodeMethod === 'feedback' ? 'rgba(236, 72, 153, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: encodeMethod === 'feedback' ? '#f472b6' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      gap: '4px',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Activity size={14} color={encodeMethod === 'feedback' ? '#ec4899' : 'var(--text-muted)'} />
                      <span style={{ fontWeight: '800' }}>Feedback Loop</span>
                    </div>
                    <span style={{ fontSize: '9px', fontWeight: '400', opacity: 0.8 }}>(Phase 17 Adv.)</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleEncodeMethodChange('scatter')}
                    style={{
                      padding: '10px 10px',
                      borderRadius: '8px',
                      border: encodeMethod === 'scatter' ? '1px solid #a855f7' : '1px solid var(--border-color)',
                      background: encodeMethod === 'scatter' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: encodeMethod === 'scatter' ? '#c084fc' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      gap: '4px',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Key size={14} color={encodeMethod === 'scatter' ? '#c084fc' : 'var(--text-muted)'} />
                      <span style={{ fontWeight: '800' }}>PRNG Scatter</span>
                    </div>
                    <span style={{ fontSize: '9px', fontWeight: '400', opacity: 0.8 }}>(Key-Randomized)</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleEncodeMethodChange('ai_adaptive')}
                    style={{
                      padding: '10px 10px',
                      borderRadius: '8px',
                      border: encodeMethod === 'ai_adaptive' ? '1px solid #38bdf8' : '1px solid var(--border-color)',
                      background: encodeMethod === 'ai_adaptive' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: encodeMethod === 'ai_adaptive' ? '#38bdf8' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      gap: '4px',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Sparkles size={14} color={encodeMethod === 'ai_adaptive' ? '#38bdf8' : 'var(--text-muted)'} />
                      <span style={{ fontWeight: '800' }}>AI RF Forest</span>
                    </div>
                    <span style={{ fontSize: '9px', fontWeight: '400', opacity: 0.8 }}>(ML Dynamic)</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleEncodeMethodChange('adaptive')}
                    style={{
                      padding: '10px 10px',
                      borderRadius: '8px',
                      border: encodeMethod === 'adaptive' ? '1px solid #06b6d4' : '1px solid var(--border-color)',
                      background: encodeMethod === 'adaptive' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: encodeMethod === 'adaptive' ? '#06b6d4' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      gap: '4px',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Zap size={14} color={encodeMethod === 'adaptive' ? '#06b6d4' : 'var(--text-muted)'} />
                      <span style={{ fontWeight: '800' }}>Rule Adaptive</span>
                    </div>
                    <span style={{ fontSize: '9px', fontWeight: '400', opacity: 0.8 }}>(Heuristic)</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleEncodeMethodChange('baseline')}
                    style={{
                      padding: '10px 10px',
                      borderRadius: '8px',
                      border: encodeMethod === 'baseline' ? '1px solid #10b981' : '1px solid var(--border-color)',
                      background: encodeMethod === 'baseline' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: encodeMethod === 'baseline' ? '#10b981' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      gap: '4px',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Shield size={14} color={encodeMethod === 'baseline' ? '#10b981' : 'var(--text-muted)'} />
                      <span style={{ fontWeight: '800' }}>Baseline LSB</span>
                    </div>
                    <span style={{ fontSize: '9px', fontWeight: '400', opacity: 0.8 }}>(Standard)</span>
                  </button>
                </div>

                {encodeMethod === 'feedback' && (
                  <div style={{ marginTop: '12px', padding: '12px 14px', background: 'rgba(236, 72, 153, 0.08)', border: '1px solid rgba(236, 72, 153, 0.3)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: '700', color: '#f472b6' }}>Adversarial Feedback Loop (Phase 17):</span>
                      <span style={{ color: '#10b981', fontWeight: '600' }}>SRM-CNN Loss Guided</span>
                    </div>
                    <div style={{ position: 'relative', marginBottom: '8px' }}>
                      <input
                        type={showEncodeKey ? 'text' : 'password'}
                        value={encodeStegoKey}
                        onChange={(e) => setEncodeStegoKey(e.target.value)}
                        placeholder="Enter secret stego key / password..."
                        style={{ width: '100%', padding: '8px 36px 8px 10px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontSize: '12px' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowEncodeKey(!showEncodeKey)}
                        style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                      >
                        {showEncodeKey ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '8px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                          Stego Cutoff τ ({feedbackThreshold})
                        </label>
                        <input
                          type="range"
                          min="0.10"
                          max="0.80"
                          step="0.05"
                          value={feedbackThreshold}
                          onChange={(e) => setFeedbackThreshold(parseFloat(e.target.value))}
                          style={{ width: '100%' }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                          Max Iterations k (1..10)
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="10"
                          value={feedbackMaxIterations}
                          onChange={(e) => setFeedbackMaxIterations(parseInt(e.target.value, 10))}
                          style={{ width: '100%', padding: '4px 8px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#fff', fontSize: '11px' }}
                        />
                      </div>
                    </div>
                    <p style={{ marginTop: '8px', fontSize: '11px' }}>
                      Interrogates the SRM-CNN Steganalyzer detector. If stego probability P(stego) &gt; τ, it adaptively throttles borderline texture blocks and tests subsequent multi-objective candidate permutations until stealth convergence.
                    </p>
                  </div>
                )}

                {encodeMethod === 'scatter' && (
                  <div style={{ marginTop: '12px', padding: '12px 14px', background: 'rgba(168, 85, 247, 0.08)', border: '1px solid rgba(168, 85, 247, 0.3)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: '700', color: '#c084fc' }}>Cryptographic PRNG Key Scatter (Phase 15):</span>
                      <span style={{ color: '#10b981', fontWeight: '600' }}>HKDF-SHA256 Seeded</span>
                    </div>
                    <div style={{ position: 'relative', marginBottom: '8px' }}>
                      <input
                        type={showEncodeKey ? 'text' : 'password'}
                        value={encodeStegoKey}
                        onChange={(e) => setEncodeStegoKey(e.target.value)}
                        placeholder="Enter secret stego key / password..."
                        style={{ width: '100%', padding: '8px 36px 8px 10px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontSize: '12px' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowEncodeKey(!showEncodeKey)}
                        style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                      >
                        {showEncodeKey ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                    <p style={{ fontSize: '11px' }}>
                      Derives a 256-bit cryptographic seed using HKDF-SHA256 to randomly permute the candidate textured blocks. Eavesdroppers without the key cannot determine traversal order or extract hidden bits.
                    </p>
                  </div>
                )}

                {encodeMethod === 'ai_adaptive' && (
                  <div style={{ marginTop: '10px', padding: '10px 12px', background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: '700', color: '#38bdf8' }}>AI Random Forest Selection (Phase 14):</span>
                      <span style={{ color: '#10b981', fontWeight: '600' }}>MSB-Invariant (Pixel & 0xFE)</span>
                    </div>
                    <p style={{ marginTop: '4px', fontSize: '11px' }}>
                      Extracts 8 spatial features per 16×16 block. Random Forest ranks textured blocks highest; smooth & flat regions are kept 100% untouched to prevent HVS visual detection and defeat steganalysis.
                    </p>
                    {encodeCapacity && encodeCapacity.ai_usable_blocks !== undefined && (
                      <div style={{ display: 'flex', gap: '12px', marginTop: '6px', fontSize: '10px', color: '#fff' }}>
                        <span>High Texture: <strong style={{ color: '#10b981' }}>{encodeCapacity.high_texture_blocks}</strong></span>
                        <span>Medium: <strong style={{ color: '#f59e0b' }}>{encodeCapacity.medium_texture_blocks}</strong></span>
                        <span>Smooth Untouched: <strong style={{ color: '#38bdf8' }}>{encodeCapacity.smooth_blocks}</strong></span>
                      </div>
                    )}
                  </div>
                )}

                {encodeMethod === 'adaptive' && (
                  <div style={{ marginTop: '10px', padding: '10px 12px', background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.2)', borderRadius: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: '600', color: '#06b6d4' }}>Rule-Based Heuristic Selection:</span>
                      <span>Block Size: 16×16 px</span>
                    </div>
                    <p style={{ marginTop: '4px', fontSize: '11px' }}>
                      Sorts 16×16 blocks by edge complexity, entropy & gradients. Flat/smooth blocks are 100% untouched to prevent visual detection.
                    </p>
                  </div>
                )}
              </div>

              {/* Secret Message Input */}
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Lock size={18} color="#06b6d4" /> 3. Secret Message Payload
              </h3>
              <textarea
                rows={5}
                placeholder="Type your confidential secret message here..."
                value={encodeMessage}
                onChange={(e) => setEncodeMessage(e.target.value)}
                style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '12px', color: '#fff', fontSize: '14px', fontFamily: 'var(--font-sans)', resize: 'vertical', marginBottom: '16px' }}
              />

              {/* Dynamic Capacity Meter */}
              {encodeCapacity && (
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                    <span style={{ color: isOversized ? '#f43f5e' : 'var(--text-secondary)' }}>
                      Payload Size: {messageSizeBytes.toLocaleString()} / {encodeCapacity.max_payload_bytes.toLocaleString()} Bytes
                    </span>
                    <span style={{ fontWeight: '700', color: isOversized ? '#f43f5e' : '#06b6d4' }}>
                      {capacityPercent}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '999px', overflow: 'hidden' }}>
                    <div style={{ width: `${capacityPercent}%`, height: '100%', background: isOversized ? '#f43f5e' : 'var(--gradient-cyber)', transition: 'width 0.2s ease' }} />
                  </div>
                  {isOversized && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f43f5e', fontSize: '12px', marginTop: '6px' }}>
                      <AlertTriangle size={14} /> Warning: Message exceeds image capacity! Choose a larger cover image.
                    </span>
                  )}
                </div>
              )}

              {encodeError && (
                <div style={{ padding: '12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', color: '#f43f5e', fontSize: '13px', marginBottom: '16px' }}>
                  {encodeError}
                </div>
              )}

              <button
                onClick={handleEncodeSubmit}
                disabled={!encodeFile || !encodeMessage.trim() || isOversized || encodeLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  background: isOversized || !encodeFile || !encodeMessage.trim() ? 'rgba(255,255,255,0.1)' : 'var(--gradient-cyber)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '15px',
                  cursor: isOversized || !encodeFile ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {encodeLoading ? <RefreshCw className="animate-spin" size={18} /> : <Lock size={18} />}
                {encodeLoading
                  ? 'Embedding Payload...'
                  : `Embed via ${
                      encodeMethod === 'feedback'
                        ? 'Feedback Loop LSB'
                        : encodeMethod === 'scatter'
                        ? 'PRNG Scatter LSB'
                        : encodeMethod === 'ai_adaptive'
                        ? 'AI RF Adaptive LSB'
                        : encodeMethod === 'adaptive'
                        ? 'Rule Adaptive LSB'
                        : 'Baseline LSB'
                    }`}
              </button>
            </div>

            {/* Output Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="#06b6d4" /> 4. Stego Image Output
              </h3>

              {encodeResult ? (
                <div>
                  <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                    <img src={encodeResult.downloadUrl} alt="Stego Output" style={{ maxHeight: '220px', borderRadius: '8px', border: '1px solid #10b981' }} />
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: '600', color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '4px 12px', borderRadius: '999px' }}>
                        <CheckCircle2 size={14} /> Ready (Lossless PNG)
                      </span>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: '600', color: '#06b6d4', background: 'rgba(6, 182, 212, 0.12)', padding: '4px 12px', borderRadius: '999px' }}>
                        {encodeResult.metadata.method === 'Key_Scattered_AI_Adaptive_LSB'
                          ? 'Method: PRNG Key-Scattered AI'
                          : encodeResult.metadata.method === 'AI_Random_Forest_Adaptive_LSB'
                            ? 'Method: AI Random Forest LSB'
                            : encodeResult.metadata.method === 'Adaptive_Rule_Based_LSB'
                              ? 'Method: Adaptive LSB'
                              : 'Method: Baseline LSB'}
                      </span>
                      {encodeResult.metadata.keyFingerprint && encodeResult.metadata.keyFingerprint !== 'Unknown' && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: '600', color: '#a855f7', background: 'rgba(168, 85, 247, 0.12)', padding: '4px 12px', borderRadius: '999px' }}>
                          <Key size={13} /> Key: {encodeResult.metadata.keyFingerprint}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Metadata Stats */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '14px' }}>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Payload Embedded</span>
                      <p style={{ fontSize: '15px', fontWeight: '700', color: '#06b6d4' }}>
                        {encodeResult.metadata.payloadBytes} Bytes
                      </p>
                    </div>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Capacity Utilized</span>
                      <p style={{ fontSize: '15px', fontWeight: '700', color: '#10b981' }}>
                        {encodeResult.metadata.capacityUsedPercent}%
                      </p>
                    </div>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>PSNR (Fidelity)</span>
                      <p style={{ fontSize: '15px', fontWeight: '700', color: '#38bdf8' }}>
                        {encodeResult.metadata.psnr !== 'Infinity' ? `${encodeResult.metadata.psnr} dB` : 'Infinity dB'}
                      </p>
                    </div>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>SSIM Structural Score</span>
                      <p style={{ fontSize: '15px', fontWeight: '700', color: '#a855f7' }}>
                        {encodeResult.metadata.ssim !== null ? encodeResult.metadata.ssim : '1.0000'}
                      </p>
                    </div>
                  </div>

                  {/* Phase 10 Adaptive Block Details if Adaptive */}
                  {encodeResult.metadata.blocksUtilized > 0 && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
                      <div style={{ padding: '8px 12px', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)', borderRadius: '8px' }}>
                        <span style={{ fontSize: '11px', color: '#06b6d4' }}>Textured Blocks Used</span>
                        <p style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>
                          {encodeResult.metadata.blocksUtilized} blocks
                        </p>
                      </div>
                      <div style={{ padding: '8px 12px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '8px' }}>
                        <span style={{ fontSize: '11px', color: '#10b981' }}>Smooth Blocks Preserved</span>
                        <p style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>
                          {encodeResult.metadata.blocksPreserved} untouched
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Quality Rating Badge */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '8px', marginBottom: '18px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Award size={18} color="#10b981" />
                      <div>
                        <span style={{ fontSize: '12px', fontWeight: '700', color: '#10b981' }}>
                          Quality Rating: {encodeResult.metadata.rating || 'EXCELLENT'}
                        </span>
                        <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {encodeResult.metadata.isImperceptible ? 'Imperceptible to Human Eye (PSNR >= 40 dB)' : 'Detectable Noise'}
                        </p>
                      </div>
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                      MSE: {encodeResult.metadata.mse !== null ? encodeResult.metadata.mse : '0.000'}
                    </span>
                  </div>

                  <a
                    href={encodeResult.downloadUrl}
                    download="stego_image.png"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      width: '100%',
                      padding: '12px',
                      background: 'rgba(16, 185, 129, 0.2)',
                      border: '1px solid #10b981',
                      borderRadius: '8px',
                      color: '#10b981',
                      fontWeight: '700',
                      fontSize: '14px',
                    }}
                  >
                    <Download size={18} /> Download Stego PNG
                  </a>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                  <Sparkles size={40} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p style={{ fontSize: '14px' }}>Upload a cover image and embed a secret message to inspect the stego result.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DECODE WORKSPACE */}
      {activeTab === 'decode' && (
        <div>
          <div style={{ marginBottom: '24px' }}>
            <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              Steganographic Extraction Workspace
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
              Upload any stego image produced by this system to extract the concealed payload and verify its integrity.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px' }}>
            {/* Decode Input */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Upload size={18} color="#06b6d4" /> 1. Upload Stego Image (PNG)
              </h3>

              <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '12px', padding: '36px 20px', textAlign: 'center', cursor: 'pointer', marginBottom: '20px', background: 'rgba(0,0,0,0.15)' }}>
                <Upload size={32} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
                <span style={{ display: 'block', fontSize: '14px', fontWeight: '600' }}>
                  {decodeFile ? decodeFile.name : 'Select Stego PNG Image'}
                </span>
                <input type="file" accept="image/png" onChange={handleDecodeImageChange} style={{ display: 'none' }} />
              </label>

              {decodePreview && (
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                  <img src={decodePreview} alt="Stego Candidate" style={{ maxHeight: '180px', borderRadius: '8px', border: '1px solid var(--border-color)' }} />
                </div>
              )}

              {/* Decode Strategy Selector */}
              <div style={{ marginBottom: '16px' }}>
                <span style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                  Extraction Method
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '6px', marginBottom: '12px' }}>
                  <button
                    type="button"
                    onClick={() => { setDecodeMethod('feedback'); setDecodeResult(null); }}
                    style={{
                      padding: '8px 8px',
                      borderRadius: '8px',
                      border: decodeMethod === 'feedback' ? '1px solid #ec4899' : '1px solid var(--border-color)',
                      background: decodeMethod === 'feedback' ? 'rgba(236, 72, 153, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: decodeMethod === 'feedback' ? '#f472b6' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    Feedback Adv. (Phase 17)
                  </button>
                  <button
                    type="button"
                    onClick={() => { setDecodeMethod('scatter'); setDecodeResult(null); }}
                    style={{
                      padding: '8px 8px',
                      borderRadius: '8px',
                      border: decodeMethod === 'scatter' ? '1px solid #a855f7' : '1px solid var(--border-color)',
                      background: decodeMethod === 'scatter' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: decodeMethod === 'scatter' ? '#c084fc' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    PRNG Scatter (Phase 15)
                  </button>
                  <button
                    type="button"
                    onClick={() => { setDecodeMethod('ai_adaptive'); setDecodeResult(null); }}
                    style={{
                      padding: '8px 8px',
                      borderRadius: '8px',
                      border: decodeMethod === 'ai_adaptive' ? '1px solid #38bdf8' : '1px solid var(--border-color)',
                      background: decodeMethod === 'ai_adaptive' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: decodeMethod === 'ai_adaptive' ? '#38bdf8' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    AI RF (Phase 14)
                  </button>
                  <button
                    type="button"
                    onClick={() => { setDecodeMethod('adaptive'); setDecodeResult(null); }}
                    style={{
                      padding: '8px 8px',
                      borderRadius: '8px',
                      border: decodeMethod === 'adaptive' ? '1px solid #06b6d4' : '1px solid var(--border-color)',
                      background: decodeMethod === 'adaptive' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: decodeMethod === 'adaptive' ? '#06b6d4' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    Rule Adaptive (Phase 10)
                  </button>
                  <button
                    type="button"
                    onClick={() => { setDecodeMethod('baseline'); setDecodeResult(null); }}
                    style={{
                      padding: '8px 8px',
                      borderRadius: '8px',
                      border: decodeMethod === 'baseline' ? '1px solid #10b981' : '1px solid var(--border-color)',
                      background: decodeMethod === 'baseline' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(0,0,0,0.2)',
                      color: decodeMethod === 'baseline' ? '#10b981' : 'var(--text-secondary)',
                      fontSize: '11px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    Baseline LSB (Phase 7)
                  </button>
                </div>

                {(decodeMethod === 'scatter' || decodeMethod === 'feedback') && (
                  <div style={{ marginBottom: '14px', padding: '12px 14px', background: decodeMethod === 'feedback' ? 'rgba(236, 72, 153, 0.08)' : 'rgba(168, 85, 247, 0.08)', border: decodeMethod === 'feedback' ? '1px solid rgba(236, 72, 153, 0.3)' : '1px solid rgba(168, 85, 247, 0.3)', borderRadius: '8px' }}>
                    <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: decodeMethod === 'feedback' ? '#f472b6' : '#c084fc', marginBottom: '6px' }}>
                      {decodeMethod === 'feedback' ? 'Steganographic Key (Auto Iteration Sync)' : 'Steganographic Secret Key (Required for Extraction)'}
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showDecodeKey ? 'text' : 'password'}
                        value={decodeStegoKey}
                        onChange={(e) => setDecodeStegoKey(e.target.value)}
                        placeholder="Enter the secret key used during embedding..."
                        style={{ width: '100%', padding: '8px 36px 8px 10px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontSize: '12px' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowDecodeKey(!showDecodeKey)}
                        style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                      >
                        {showDecodeKey ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                    {decodeMethod === 'feedback' && (
                      <p style={{ marginTop: '6px', fontSize: '10px', color: 'var(--text-muted)' }}>
                        Receiver auto-probes candidate iteration salts (k=1..k_max) to recover exact permutation order without any side-channel transmissions.
                      </p>
                    )}
                  </div>
                )}
              </div>

              {decodeError && (
                <div style={{ padding: '12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', color: '#f43f5e', fontSize: '13px', marginBottom: '16px' }}>
                  {decodeError}
                </div>
              )}

              <button
                onClick={handleDecodeSubmit}
                disabled={!decodeFile || decodeLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  background: !decodeFile ? 'rgba(255,255,255,0.1)' : 'var(--gradient-cyber)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '15px',
                  cursor: !decodeFile ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {decodeLoading ? <RefreshCw className="animate-spin" size={18} /> : <FileText size={18} />}
                {decodeLoading ? 'Extracting Payload...' : `Extract via ${decodeMethod === 'feedback' ? 'Feedback Adv. LSB' : decodeMethod === 'scatter' ? 'PRNG Scatter LSB' : decodeMethod === 'ai_adaptive' ? 'AI Adaptive LSB' : decodeMethod === 'adaptive' ? 'Rule Adaptive LSB' : 'Baseline LSB'}`}
              </button>
            </div>

            {/* Extracted Message Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={18} color="#10b981" /> 2. Extracted Secret Payload
              </h3>

              {decodeResult ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: '600', color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '4px 10px', borderRadius: '999px' }}>
                        <CheckCircle2 size={14} /> CRC-32 Integrity Verified
                      </span>
                      {decodeResult.opt_iteration !== undefined && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#ec4899', background: 'rgba(236, 72, 153, 0.12)', padding: '4px 8px', borderRadius: '999px' }}>
                          <RefreshCw size={12} /> Sync Iteration: k={decodeResult.opt_iteration}
                        </span>
                      )}
                      {decodeResult.key_fingerprint && decodeResult.key_fingerprint !== 'Unknown' && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#a855f7', background: 'rgba(168, 85, 247, 0.12)', padding: '4px 8px', borderRadius: '999px' }}>
                          <Key size={12} /> Key: {decodeResult.key_fingerprint}
                        </span>
                      )}
                      {decodeResult.blocks_traversed && (
                        <span style={{ fontSize: '11px', color: '#06b6d4', background: 'rgba(6, 182, 212, 0.12)', padding: '4px 8px', borderRadius: '999px' }}>
                          {decodeResult.blocks_traversed} Blocks Traversed
                        </span>
                      )}
                    </div>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      Length: {decodeResult.payload_bytes} Bytes
                    </span>
                  </div>

                  <div style={{ position: 'relative', marginBottom: '16px' }}>
                    <textarea
                      readOnly
                      rows={6}
                      value={decodeResult.payload_text || '(Binary Payload)'}
                      style={{
                        width: '100%',
                        background: 'rgba(0,0,0,0.4)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '8px',
                        padding: '12px',
                        color: '#06b6d4',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '13px',
                      }}
                    />
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(decodeResult.payload_text || '');
                        setCopiedDecoded(true);
                        setTimeout(() => setCopiedDecoded(false), 2000);
                      }}
                      style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        padding: '6px 10px',
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        color: '#fff',
                        fontSize: '11px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      {copiedDecoded ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                      {copiedDecoded ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                  <FileText size={40} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p style={{ fontSize: '14px' }}>Upload a stego image to extract and verify the hidden plaintext.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB: ROBUSTNESS & CHANNEL PERTURBATION PROFILING (PHASE 19) */}
      {activeTab === 'robustness' && (
        <div>
          {/* Header */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: '800', color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', padding: '4px 10px', borderRadius: '999px', letterSpacing: '0.5px' }}>
                    <AlertTriangle size={13} /> PHASE 19 FORENSIC LAB
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Channel Attack Simulation & Tamper-Evident Verification
                  </span>
                </div>
                <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
                  Robustness & Noise Perturbation Profiling
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '15px', maxWidth: '850px' }}>
                  Simulate real-world channel noise, lossy JPEG compression, and spatial filtering attacks to quantify visual degradation, spatial LSB corruption rates, and cryptographic tamper detection.
                </p>
              </div>

              {(pipelineResult?.blob || encodeResult?.blob) && (
                <button
                  type="button"
                  onClick={handleUseLastPipelineStego}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    background: 'rgba(6, 182, 212, 0.15)',
                    border: '1px solid rgba(6, 182, 212, 0.35)',
                    color: '#06b6d4',
                    fontSize: '13px',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  <Sparkles size={16} /> Load Last Encoded Stego Image
                </button>
              )}
            </div>
          </div>

          {/* Main Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px', marginBottom: '32px' }}>
            {/* Left Column: Attack Configuration Studio */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={18} color="#f59e0b" /> 1. Channel Attack & Extraction Parameters
              </h3>

              {/* Stego File Dropzone */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Candidate Stego Image (PNG)
                </label>
                <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '10px', padding: '16px 12px', textAlign: 'center', cursor: 'pointer', background: 'rgba(0,0,0,0.15)' }}>
                  {robustStegoPreview ? (
                    <img src={robustStegoPreview} alt="Stego Preview" style={{ maxHeight: '120px', margin: '0 auto 8px', borderRadius: '6px' }} />
                  ) : (
                    <Upload size={24} color="var(--text-muted)" style={{ margin: '0 auto 8px' }} />
                  )}
                  <span style={{ display: 'block', fontSize: '12px', fontWeight: '600' }}>
                    {robustStegoFile ? robustStegoFile.name : 'Select Stego PNG for Attack Testing'}
                  </span>
                  <input type="file" accept="image/png" onChange={handleRobustFileChange} style={{ display: 'none' }} />
                </label>
              </div>

              {/* Attack Type Selector (5 Cards) */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Perturbation Attack Mode
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '8px' }}>
                  {[
                    { id: 'gaussian', name: 'Gaussian Noise', desc: 'N(0, σ²)' },
                    { id: 'salt_pepper', name: 'Salt & Pepper', desc: 'Impulse Noise' },
                    { id: 'jpeg', name: 'JPEG Compress', desc: 'Lossy DCT (Q)' },
                    { id: 'blur', name: 'Gaussian Blur', desc: 'Low-Pass Filter' },
                    { id: 'speckle', name: 'Speckle Noise', desc: 'Multiplicative' },
                  ].map(atk => (
                    <button
                      key={atk.id}
                      type="button"
                      onClick={() => setRobustAttackType(atk.id)}
                      style={{
                        padding: '10px 8px',
                        borderRadius: '8px',
                        border: robustAttackType === atk.id ? '1px solid #f59e0b' : '1px solid var(--border-color)',
                        background: robustAttackType === atk.id ? 'rgba(245, 158, 11, 0.15)' : 'rgba(0,0,0,0.2)',
                        color: robustAttackType === atk.id ? '#fbbf24' : 'var(--text-secondary)',
                        fontSize: '11px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        textAlign: 'center',
                      }}
                    >
                      <div>{atk.name}</div>
                      <span style={{ fontSize: '9px', opacity: 0.75 }}>{atk.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic Attack Parameter Sliders */}
              <div style={{ marginBottom: '20px', padding: '14px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                {robustAttackType === 'gaussian' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '600' }}>Noise Standard Deviation (σ)</span>
                      <span style={{ color: '#fbbf24', fontWeight: '800' }}>σ = {robustStd}</span>
                    </div>
                    <input
                      type="range"
                      min="0.2"
                      max="10.0"
                      step="0.2"
                      value={robustStd}
                      onChange={(e) => setRobustStd(e.target.value)}
                      style={{ width: '100%', accentColor: '#f59e0b' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      <span>Subtle (0.2)</span>
                      <span>Moderate (2.0)</span>
                      <span>Heavy (10.0)</span>
                    </div>
                  </div>
                )}

                {robustAttackType === 'salt_pepper' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '600' }}>Impulse Pixel Density (p)</span>
                      <span style={{ color: '#fbbf24', fontWeight: '800' }}>{(robustDensity * 100).toFixed(1)}% pixels</span>
                    </div>
                    <input
                      type="range"
                      min="0.001"
                      max="0.10"
                      step="0.002"
                      value={robustDensity}
                      onChange={(e) => setRobustDensity(e.target.value)}
                      style={{ width: '100%', accentColor: '#f59e0b' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      <span>0.1%</span>
                      <span>2.0%</span>
                      <span>10.0%</span>
                    </div>
                  </div>
                )}

                {robustAttackType === 'jpeg' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '600' }}>JPEG Quality Factor (Q)</span>
                      <span style={{ color: '#fbbf24', fontWeight: '800' }}>Q = {robustJpegQuality}</span>
                    </div>
                    <input
                      type="range"
                      min="30"
                      max="95"
                      step="5"
                      value={robustJpegQuality}
                      onChange={(e) => setRobustJpegQuality(e.target.value)}
                      style={{ width: '100%', accentColor: '#f59e0b' }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      <span>Heavy Quantization (Q=30)</span>
                      <span>Standard Web (Q=75)</span>
                      <span>Near-Lossless (Q=95)</span>
                    </div>
                  </div>
                )}

                {robustAttackType === 'blur' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '600' }}>Gaussian Kernel Sigma (σ)</span>
                      <span style={{ color: '#fbbf24', fontWeight: '800' }}>σ = {robustBlurSigma}</span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="3.0"
                      step="0.25"
                      value={robustBlurSigma}
                      onChange={(e) => setRobustBlurSigma(e.target.value)}
                      style={{ width: '100%', accentColor: '#f59e0b' }}
                    />
                  </div>
                )}

                {robustAttackType === 'speckle' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '600' }}>Multiplicative Noise Sigma (σ)</span>
                      <span style={{ color: '#fbbf24', fontWeight: '800' }}>σ = {robustSpeckleStd}</span>
                    </div>
                    <input
                      type="range"
                      min="0.01"
                      max="0.20"
                      step="0.01"
                      value={robustSpeckleStd}
                      onChange={(e) => setRobustSpeckleStd(e.target.value)}
                      style={{ width: '100%', accentColor: '#f59e0b' }}
                    />
                  </div>
                )}
              </div>

              {/* Extraction Strategy & Credentials */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Extraction Verification Strategy
                </label>
                <select
                  value={robustExtractionMethod}
                  onChange={(e) => setRobustExtractionMethod(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontSize: '12px', marginBottom: '12px' }}
                >
                  <option value="scatter">PRNG Key-Based Random Block Scatter</option>
                  <option value="pipeline_hybrid">Unified One-Click Hybrid Pipeline (RSA-4096 + AES-256-GCM)</option>
                  <option value="ai_adaptive">AI-Adaptive Dynamic LSB (Random Forest)</option>
                  <option value="adaptive">Rule-Based Spatial Adaptive LSB</option>
                  <option value="baseline">Baseline Sequential LSB</option>
                  <option value="none">Visual Distortion Profile Only (Skip Extraction)</option>
                </select>

                {robustExtractionMethod === 'scatter' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      Steganographic Passphrase / Key
                    </label>
                    <input
                      type="text"
                      value={robustStegoKey}
                      onChange={(e) => setRobustStegoKey(e.target.value)}
                      placeholder="SecretStegoPassphrase#2026"
                      style={{ width: '100%', padding: '8px 10px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontSize: '12px' }}
                    />
                  </div>
                )}

                {robustExtractionMethod === 'pipeline_hybrid' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <label style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)' }}>
                        Recipient RSA-4096 Private Key PEM
                      </label>
                      {vaultPrivateKey && (
                        <button
                          type="button"
                          onClick={() => setRobustPrivateKeyPem(vaultPrivateKey)}
                          style={{ background: 'none', border: 'none', color: '#06b6d4', fontSize: '11px', cursor: 'pointer', textDecoration: 'underline' }}
                        >
                          Use My Vault Private Key
                        </button>
                      )}
                    </div>
                    <textarea
                      rows={3}
                      value={robustPrivateKeyPem}
                      onChange={(e) => setRobustPrivateKeyPem(e.target.value)}
                      placeholder="-----BEGIN RSA PRIVATE KEY-----"
                      style={{ width: '100%', padding: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#a855f7', fontFamily: 'var(--font-mono)', fontSize: '10px' }}
                    />
                  </div>
                )}
              </div>

              {robustError && (
                <div style={{ padding: '10px 12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '6px', color: '#f43f5e', fontSize: '12px', marginBottom: '14px' }}>
                  {robustError}
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <button
                  type="button"
                  onClick={handleRunAttackAndProfile}
                  disabled={!robustStegoFile || robustLoading}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    background: !robustStegoFile ? 'rgba(255,255,255,0.1)' : 'var(--gradient-cyber)',
                    color: '#fff',
                    fontWeight: '700',
                    fontSize: '13px',
                    cursor: !robustStegoFile ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  <AlertTriangle size={15} /> {robustLoading ? 'Simulating...' : 'Profile Attack'}
                </button>

                <button
                  type="button"
                  onClick={handleRunSweep}
                  disabled={!robustStegoFile || robustSweepLoading}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    border: '1px solid rgba(245, 158, 11, 0.35)',
                    color: '#fbbf24',
                    fontWeight: '700',
                    fontSize: '13px',
                    cursor: !robustStegoFile ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  <BarChart2 size={15} /> {robustSweepLoading ? 'Sweeping...' : '5-Point Sweep'}
                </button>
              </div>
            </div>

            {/* Right Column: Forensic Results Dashboard */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={18} color="#06b6d4" /> 2. Forensic Distortion & Tamper Verification
              </h3>

              {robustProfileReport ? (
                <div>
                  {/* Tamper Alert Banner */}
                  <div
                    style={{
                      padding: '16px',
                      borderRadius: '10px',
                      marginBottom: '20px',
                      background: robustProfileReport.tamper_detected
                        ? 'rgba(239, 68, 68, 0.15)'
                        : 'rgba(16, 185, 129, 0.15)',
                      border: `1px solid ${robustProfileReport.tamper_detected ? 'rgba(239, 68, 68, 0.35)' : 'rgba(16, 185, 129, 0.35)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    {robustProfileReport.tamper_detected ? (
                      <AlertTriangle size={28} color="#ef4444" style={{ flexShrink: 0 }} />
                    ) : (
                      <CheckCircle2 size={28} color="#10b981" style={{ flexShrink: 0 }} />
                    )}
                    <div>
                      <h4 style={{ fontSize: '15px', fontWeight: '800', color: robustProfileReport.tamper_detected ? '#f87171' : '#34d399', marginBottom: '3px' }}>
                        {robustProfileReport.tamper_detected
                          ? 'ACTIVE TAMPERING / ATTACK DETECTED'
                          : 'INTEGRITY VERIFIED: PAYLOAD INTACT'}
                      </h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                        {robustProfileReport.integrity_message}
                      </p>
                    </div>
                  </div>

                  {/* Tri-View Images (Stego, Perturbed, Amplified Difference) */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '20px' }}>
                    <div style={{ textAlign: 'center' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Original Stego</span>
                      {robustStegoPreview && (
                        <img src={robustStegoPreview} alt="Original Stego" style={{ width: '100%', maxHeight: '110px', objectFit: 'cover', borderRadius: '6px', border: '1px solid var(--border-color)' }} />
                      )}
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <span style={{ fontSize: '11px', color: '#fbbf24', display: 'block', marginBottom: '4px' }}>Perturbed ({robustAttackType})</span>
                      {robustPerturbedUrl && (
                        <img src={robustPerturbedUrl} alt="Perturbed Stego" style={{ width: '100%', maxHeight: '110px', objectFit: 'cover', borderRadius: '6px', border: '1px solid rgba(245, 158, 11, 0.4)' }} />
                      )}
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <span style={{ fontSize: '11px', color: '#ec4899', display: 'block', marginBottom: '4px' }}>Residual Diff (15x)</span>
                      {robustDiffUrl && (
                        <img src={robustDiffUrl} alt="Difference Residual" style={{ width: '100%', maxHeight: '110px', objectFit: 'cover', borderRadius: '6px', border: '1px solid rgba(236, 72, 153, 0.4)' }} />
                      )}
                    </div>
                  </div>

                  {/* 4-Stat Metrics Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '20px' }}>
                    <div style={{ padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Degraded PSNR</span>
                      <p style={{ fontSize: '18px', fontWeight: '800', color: robustProfileReport.degraded_psnr_db >= 40 ? '#10b981' : robustProfileReport.degraded_psnr_db >= 35 ? '#f59e0b' : '#ef4444' }}>
                        {robustProfileReport.degraded_psnr_db} dB
                      </p>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Rating: {robustProfileReport.quality_rating}</span>
                    </div>

                    <div style={{ padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Degraded SSIM</span>
                      <p style={{ fontSize: '18px', fontWeight: '800', color: robustProfileReport.degraded_ssim >= 0.98 ? '#10b981' : '#f59e0b' }}>
                        {robustProfileReport.degraded_ssim.toFixed(4)}
                      </p>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>MSE: {robustProfileReport.degraded_mse.toFixed(2)}</span>
                    </div>

                    <div style={{ padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>LSB Bit Alteration Rate</span>
                      <p style={{ fontSize: '18px', fontWeight: '800', color: robustProfileReport.lsb_ber > 0.05 ? '#f43f5e' : '#10b981' }}>
                        {(robustProfileReport.lsb_ber * 100).toFixed(2)}%
                      </p>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Spatial LSB plane flipped</span>
                    </div>

                    <div style={{ padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Survival Status</span>
                      <p style={{ fontSize: '15px', fontWeight: '800', color: robustProfileReport.survival_status === 'INTACT' ? '#10b981' : '#f43f5e' }}>
                        {robustProfileReport.survival_status}
                      </p>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Latency: {robustProfileReport.execution_time_ms} ms</span>
                    </div>
                  </div>

                  {/* Download Perturbed Stego Button */}
                  {robustPerturbedBlob && (
                    <button
                      type="button"
                      onClick={handleDownloadPerturbed}
                      style={{
                        width: '100%',
                        padding: '10px',
                        borderRadius: '6px',
                        background: 'rgba(255,255,255,0.08)',
                        border: '1px solid var(--border-color)',
                        color: '#fff',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        marginBottom: '16px',
                      }}
                    >
                      <Download size={14} /> Download Perturbed Stego Image ({robustAttackType})
                    </button>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                  <AlertTriangle size={42} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p style={{ fontSize: '14px', marginBottom: '6px' }}>Select an attack and click Profile Attack to test resilience.</p>
                  <p style={{ fontSize: '12px', opacity: 0.7 }}>Observe visual degradation, spatial LSB corruption, and cryptographic tamper detection.</p>
                </div>
              )}

              {/* 5-Point Parameter Sweep Table */}
              {robustSweepData && robustSweepData.length > 0 && (
                <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <BarChart2 size={16} color="#fbbf24" /> Multi-Level Degradation Sweep ({robustAttackType})
                  </h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                          <th style={{ padding: '6px 8px' }}>Intensity</th>
                          <th style={{ padding: '6px 8px' }}>PSNR (dB)</th>
                          <th style={{ padding: '6px 8px' }}>SSIM</th>
                          <th style={{ padding: '6px 8px' }}>LSB BER</th>
                          <th style={{ padding: '6px 8px' }}>Tamper</th>
                          <th style={{ padding: '6px 8px' }}>Survival</th>
                        </tr>
                      </thead>
                      <tbody>
                        {robustSweepData.map((pt, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                            <td style={{ padding: '6px 8px', fontWeight: '700', color: '#fbbf24' }}>{pt.attack_intensity}</td>
                            <td style={{ padding: '6px 8px' }}>{pt.degraded_psnr_db}</td>
                            <td style={{ padding: '6px 8px' }}>{pt.degraded_ssim}</td>
                            <td style={{ padding: '6px 8px', color: pt.lsb_ber > 0.1 ? '#f43f5e' : '#10b981' }}>{(pt.lsb_ber * 100).toFixed(1)}%</td>
                            <td style={{ padding: '6px 8px', color: pt.tamper_detected ? '#f43f5e' : '#10b981', fontWeight: '700' }}>
                              {pt.tamper_detected ? 'DETECTED' : 'CLEAN'}
                            </td>
                            <td style={{ padding: '6px 8px', color: pt.survival_status === 'INTACT' ? '#10b981' : '#f43f5e' }}>{pt.survival_status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB: MULTI-OBJECTIVE GENETIC / PARETO OPTIMIZER (PHASE 20) */}
      {activeTab === 'optimizer' && (
        <div>
          {/* Header */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: '800', color: '#10b981', background: 'rgba(16, 185, 129, 0.15)', padding: '4px 10px', borderRadius: '999px', letterSpacing: '0.5px' }}>
                    <Target size={13} /> PHASE 20 META-HEURISTIC SEARCH
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Multi-Objective Genetic Algorithm & Pareto Frontier
                  </span>
                </div>
                <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
                  Multi-Objective Genetic & Pareto Optimization
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '15px', maxWidth: '850px' }}>
                  Evolves steganographic hyper-parameters (block size, texture bit allocation depths, CNN decision threshold τ) to discover the non-dominated Pareto frontier balancing PSNR, SSIM, Capacity, and Adversarial Stealth.
                </p>
              </div>

              {optAppliedAlert && (
                <div style={{ padding: '8px 16px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.2)', border: '1px solid #10b981', color: '#34d399', fontSize: '13px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={16} /> Parameters Transferred! Redirecting to Embed Workspace...
                </div>
              )}
            </div>
          </div>

          {/* Main Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px', marginBottom: '32px' }}>
            {/* Left Column: Evolutionary Configuration Studio */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Compass size={18} color="#10b981" /> 1. Search Space & Priority Objectives
              </h3>

              {/* Cover Image Dropzone */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Reference Cover Image (PNG)
                </label>
                <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '10px', padding: '16px 12px', textAlign: 'center', cursor: 'pointer', background: 'rgba(0,0,0,0.15)' }}>
                  {optCoverPreview ? (
                    <img src={optCoverPreview} alt="Cover Preview" style={{ maxHeight: '120px', margin: '0 auto 8px', borderRadius: '6px' }} />
                  ) : (
                    <Upload size={24} color="var(--text-muted)" style={{ margin: '0 auto 8px' }} />
                  )}
                  <span style={{ display: 'block', fontSize: '12px', fontWeight: '600' }}>
                    {optCoverFile ? optCoverFile.name : 'Select Cover PNG for Evolutionary Search'}
                  </span>
                  <input type="file" accept="image/png" onChange={handleOptCoverChange} style={{ display: 'none' }} />
                </label>
              </div>

              {/* Test Secret Message Payload */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Target Payload for Evolutionary Fitness
                </label>
                <textarea
                  rows={2}
                  value={optMessage}
                  onChange={(e) => setOptMessage(e.target.value)}
                  placeholder="Enter secret message to evaluate capacity and distortion..."
                  style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '8px 10px', color: '#fff', fontSize: '12px', resize: 'vertical' }}
                />
              </div>

              {/* Research Priority Profile Selector (4 Cards) */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Multi-Objective Research Priority
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
                  {[
                    { id: 'Balanced', name: 'Balanced Search', weights: 'w=[0.25, 0.25, 0.25, 0.25]' },
                    { id: 'Quality', name: 'Quality Priority', weights: 'w1=0.40, w2=0.40 (PSNR/SSIM)' },
                    { id: 'Security', name: 'Stealth Priority', weights: 'w4=0.50 (Anti-Steganalysis)' },
                    { id: 'Capacity', name: 'Capacity Priority', weights: 'w3=0.50 (Max Utilization)' },
                  ].map(p => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setOptProfile(p.id)}
                      style={{
                        padding: '10px 8px',
                        borderRadius: '8px',
                        border: optProfile === p.id ? '1px solid #10b981' : '1px solid var(--border-color)',
                        background: optProfile === p.id ? 'rgba(16, 185, 129, 0.15)' : 'rgba(0,0,0,0.2)',
                        color: optProfile === p.id ? '#34d399' : 'var(--text-secondary)',
                        fontSize: '11px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      <div>{p.name}</div>
                      <span style={{ fontSize: '9px', opacity: 0.75 }}>{p.weights}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Genetic Algorithm Controls (Generations & Population) */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '18px', padding: '14px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '6px' }}>
                    <span style={{ fontWeight: '600' }}>Generations (G)</span>
                    <span style={{ color: '#34d399', fontWeight: '800' }}>{optGenerations} gens</span>
                  </div>
                  <input
                    type="range"
                    min="2"
                    max="6"
                    step="1"
                    value={optGenerations}
                    onChange={(e) => setOptGenerations(parseInt(e.target.value, 10))}
                    style={{ width: '100%', accentColor: '#10b981' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '6px' }}>
                    <span style={{ fontWeight: '600' }}>Population (N)</span>
                    <span style={{ color: '#34d399', fontWeight: '800' }}>{optPopulationSize} candidates</span>
                  </div>
                  <input
                    type="range"
                    min="4"
                    max="12"
                    step="2"
                    value={optPopulationSize}
                    onChange={(e) => setOptPopulationSize(parseInt(e.target.value, 10))}
                    style={{ width: '100%', accentColor: '#10b981' }}
                  />
                </div>
              </div>

              {/* Stego Passphrase */}
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Evaluation Steganographic Key
                </label>
                <input
                  type="text"
                  value={optStegoKey}
                  onChange={(e) => setOptStegoKey(e.target.value)}
                  placeholder="GeneticOptimizerKey#2026"
                  style={{ width: '100%', padding: '8px 10px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontSize: '12px' }}
                />
              </div>

              {optError && (
                <div style={{ padding: '10px 12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '6px', color: '#f43f5e', fontSize: '12px', marginBottom: '14px' }}>
                  {optError}
                </div>
              )}

              {/* Action Button */}
              <button
                type="button"
                onClick={handleRunGeneticOptimization}
                disabled={!optCoverFile || !optMessage.trim() || optLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  background: !optCoverFile || !optMessage.trim() ? 'rgba(255,255,255,0.1)' : 'var(--gradient-cyber)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '13px',
                  cursor: !optCoverFile || !optMessage.trim() ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <Target size={16} /> {optLoading ? 'Evolving Generations...' : 'Run Evolutionary Parameter Search'}
              </button>
            </div>

            {/* Right Column: Pareto Frontier & Results Dashboard */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={18} color="#06b6d4" /> 2. Pareto Frontier & Discovered Optimum
              </h3>

              {optResult ? (
                <div>
                  {/* Optimal Solution Card */}
                  <div
                    style={{
                      padding: '16px 20px',
                      borderRadius: '10px',
                      marginBottom: '20px',
                      background: 'rgba(16, 185, 129, 0.12)',
                      border: '1px solid rgba(16, 185, 129, 0.35)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Award size={22} color="#10b981" />
                        <div>
                          <h4 style={{ fontSize: '15px', fontWeight: '800', color: '#34d399', margin: 0 }}>
                            OPTIMAL CONFIGURATION DISCOVERED
                          </h4>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            Fitness Score S = {optResult.best_evaluation.fitness_score} across {optResult.generations_run} generations
                          </span>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={handleApplyOptimizedToEmbed}
                        style={{
                          padding: '7px 14px',
                          borderRadius: '6px',
                          background: 'var(--gradient-cyber)',
                          color: '#fff',
                          fontWeight: '700',
                          fontSize: '11px',
                          cursor: 'pointer',
                          border: 'none',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <Zap size={13} /> Apply to Embed Workspace
                      </button>
                    </div>

                    {/* Gene Pills */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', fontSize: '11px', color: '#06b6d4', fontWeight: '600' }}>
                        Block Size: {optResult.best_evaluation.chromosome.block_size}×{optResult.best_evaluation.chromosome.block_size}
                      </span>
                      <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', fontSize: '11px', color: '#ec4899', fontWeight: '600' }}>
                        High Texture: {optResult.best_evaluation.chromosome.bits_high_texture} bpp
                      </span>
                      <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', fontSize: '11px', color: '#fbbf24', fontWeight: '600' }}>
                        Medium Texture: {optResult.best_evaluation.chromosome.bits_medium} bpp
                      </span>
                      <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', fontSize: '11px', color: '#a855f7', fontWeight: '600' }}>
                        Smooth: {optResult.best_evaluation.chromosome.bits_smooth} bpp
                      </span>
                      <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', fontSize: '11px', color: '#38bdf8', fontWeight: '600' }}>
                        Cutoff τ: {optResult.best_evaluation.chromosome.decision_threshold}
                      </span>
                    </div>
                  </div>

                  {/* 4-Stat Radar Scoreboard */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '20px' }}>
                    <div style={{ padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Visual Fidelity (PSNR)</span>
                      <p style={{ fontSize: '18px', fontWeight: '800', color: optResult.best_evaluation.psnr_db >= 45 ? '#10b981' : '#f59e0b' }}>
                        {optResult.best_evaluation.psnr_db} dB
                      </p>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Rating: {optResult.best_evaluation.quality_rating}</span>
                    </div>

                    <div style={{ padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Structural Similarity (SSIM)</span>
                      <p style={{ fontSize: '18px', fontWeight: '800', color: optResult.best_evaluation.ssim >= 0.99 ? '#10b981' : '#06b6d4' }}>
                        {optResult.best_evaluation.ssim.toFixed(4)}
                      </p>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>MSE: {optResult.best_evaluation.mse.toFixed(2)}</span>
                    </div>

                    <div style={{ padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Steganalysis Stealth</span>
                      <p style={{ fontSize: '18px', fontWeight: '800', color: optResult.best_evaluation.p_stego < 0.35 ? '#10b981' : '#f43f5e' }}>
                        {((1.0 - optResult.best_evaluation.p_stego) * 100).toFixed(1)}%
                      </p>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>P(stego): {(optResult.best_evaluation.p_stego * 100).toFixed(1)}%</span>
                    </div>

                    <div style={{ padding: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Capacity Packing</span>
                      <p style={{ fontSize: '18px', fontWeight: '800', color: '#a855f7' }}>
                        {(optResult.best_evaluation.capacity_used_ratio * 100).toFixed(1)}%
                      </p>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Search Latency: {optResult.execution_time_ms} ms</span>
                    </div>
                  </div>

                  {/* Generational Convergence Progression Table */}
                  <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ fontSize: '13px', fontWeight: '700', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <TrendingUp size={15} color="#10b981" /> Generational Convergence
                    </h4>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                            <th style={{ padding: '5px 8px' }}>Gen</th>
                            <th style={{ padding: '5px 8px' }}>Best S</th>
                            <th style={{ padding: '5px 8px' }}>Avg S</th>
                            <th style={{ padding: '5px 8px' }}>Best PSNR</th>
                            <th style={{ padding: '5px 8px' }}>Best P(stego)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {optResult.convergence_history.map((snap) => (
                            <tr key={snap.generation} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                              <td style={{ padding: '5px 8px', fontWeight: '700', color: '#10b981' }}>G{snap.generation}</td>
                              <td style={{ padding: '5px 8px', fontWeight: '700', color: '#34d399' }}>{snap.best_fitness}</td>
                              <td style={{ padding: '5px 8px', color: 'var(--text-muted)' }}>{snap.avg_fitness}</td>
                              <td style={{ padding: '5px 8px' }}>{snap.best_psnr_db} dB</td>
                              <td style={{ padding: '5px 8px', color: snap.best_p_stego < 0.35 ? '#10b981' : '#f59e0b' }}>
                                {(snap.best_p_stego * 100).toFixed(1)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Pareto Tradeoff Frontier */}
                  {optResult.pareto_front && optResult.pareto_front.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: '13px', fontWeight: '700', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Target size={15} color="#06b6d4" /> Non-Dominated Pareto Frontier (Fidelity vs. Stealth)
                      </h4>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse', textAlign: 'left' }}>
                          <thead>
                            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                              <th style={{ padding: '5px 8px' }}>Block</th>
                              <th style={{ padding: '5px 8px' }}>Depths (H/M/S)</th>
                              <th style={{ padding: '5px 8px' }}>PSNR</th>
                              <th style={{ padding: '5px 8px' }}>SSIM</th>
                              <th style={{ padding: '5px 8px' }}>Stealth (1-P)</th>
                              <th style={{ padding: '5px 8px' }}>Fitness S</th>
                            </tr>
                          </thead>
                          <tbody>
                            {optResult.pareto_front.map((pt, idx) => (
                              <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                <td style={{ padding: '5px 8px', fontWeight: '600' }}>{pt.chromosome.block_size}×{pt.chromosome.block_size}</td>
                                <td style={{ padding: '5px 8px', color: '#ec4899' }}>
                                  {pt.chromosome.bits_high_texture}/{pt.chromosome.bits_medium}/{pt.chromosome.bits_smooth}
                                </td>
                                <td style={{ padding: '5px 8px', fontWeight: '700', color: '#10b981' }}>{pt.psnr_db} dB</td>
                                <td style={{ padding: '5px 8px' }}>{pt.ssim.toFixed(4)}</td>
                                <td style={{ padding: '5px 8px', color: '#06b6d4' }}>{(pt.stealth_score * 100).toFixed(1)}%</td>
                                <td style={{ padding: '5px 8px', fontWeight: '700', color: '#fbbf24' }}>{pt.fitness_score}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                  <Target size={42} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p style={{ fontSize: '14px', marginBottom: '6px' }}>Select an image and click Run Evolutionary Search to find optimal parameters.</p>
                  <p style={{ fontSize: '12px', opacity: 0.7 }}>Discovers the optimal trade-off between imperceptibility, stealth, and capacity.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB: AI REGION SUITABILITY & HEATMAP STUDIO (PHASE 13) */}
      {activeTab === 'ai-regions' && (
        <div>
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
                  AI Region Suitability & Heatmap Studio
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
                  Trained Random Forest Classifier (Phase 12) partitions cover images into 16×16 blocks and predicts embedding suitability across 8 spatial complexity features.
                </p>
              </div>
              <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '999px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                ML Inference Active (Random Forest)
              </span>
            </div>
          </div>

          {/* Model Specs Banner */}
          <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Cpu size={24} color="#06b6d4" />
              <div>
                <span style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>
                  Model: Random Forest Classifier (100 Trees, max_depth=12)
                </span>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Trained on 3,000 balanced spatial feature vectors. Test Accuracy: 100.00% | Multiclass ROC-AUC: 1.0000
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '12px', fontSize: '12px' }}>
              <span style={{ color: '#06b6d4' }}>Features: 8 Spatial Metrics</span>
              <span style={{ color: '#10b981' }}>MSB-Plane Invariant</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px' }}>
            {/* Input Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Upload size={18} color="#06b6d4" /> 1. Upload Cover Image (PNG)
              </h3>

              <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '12px', padding: '32px 20px', textAlign: 'center', cursor: 'pointer', marginBottom: '20px', background: 'rgba(0,0,0,0.15)' }}>
                <Upload size={32} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
                <span style={{ display: 'block', fontSize: '14px', fontWeight: '600' }}>
                  {aiImageFile ? aiImageFile.name : 'Select PNG Image for AI Inspection'}
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Lossless PNG recommended</span>
                <input type="file" accept="image/png" onChange={handleAiImageChange} style={{ display: 'none' }} />
              </label>

              {aiImagePreview && (
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                  <img src={aiImagePreview} alt="Cover Preview" style={{ maxHeight: '180px', borderRadius: '8px', border: '1px solid var(--border-color)' }} />
                </div>
              )}

              {/* Settings */}
              <div style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', marginBottom: '20px', fontSize: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Block Partition Size:</span>
                  <span style={{ fontWeight: '700', color: '#fff' }}>16 × 16 pixels</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Feature Extraction:</span>
                  <span style={{ fontWeight: '700', color: '#06b6d4' }}>Upper 7 MSB (Pixel & 0xFE)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Heatmap Alpha Opacity:</span>
                  <span style={{ fontWeight: '700', color: '#10b981' }}>45% Semi-Transparent</span>
                </div>
              </div>

              {aiHeatmapError && (
                <div style={{ padding: '12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', color: '#f43f5e', fontSize: '13px', marginBottom: '16px' }}>
                  {aiHeatmapError}
                </div>
              )}

              <button
                onClick={handleAiAnalyzeSubmit}
                disabled={!aiImageFile || aiHeatmapLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  background: !aiImageFile ? 'rgba(255,255,255,0.1)' : 'var(--gradient-cyber)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '15px',
                  cursor: !aiImageFile ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {aiHeatmapLoading ? <RefreshCw className="animate-spin" size={18} /> : <Sparkles size={18} />}
                {aiHeatmapLoading ? 'Running AI Classification...' : 'Analyze Regions & Generate Heatmap'}
              </button>
            </div>

            {/* Output Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Eye size={18} color="#10b981" /> 2. AI Visual Heatmap Overlay
                </h3>
                {aiHeatmapUrl && (
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={() => setAiViewMode('heatmap')}
                      style={{
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '600',
                        background: aiViewMode === 'heatmap' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
                        color: aiViewMode === 'heatmap' ? '#10b981' : 'var(--text-muted)',
                        border: '1px solid var(--border-color)',
                        cursor: 'pointer',
                      }}
                    >
                      Heatmap
                    </button>
                    <button
                      type="button"
                      onClick={() => setAiViewMode('original')}
                      style={{
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '600',
                        background: aiViewMode === 'original' ? 'rgba(6, 182, 212, 0.2)' : 'transparent',
                        color: aiViewMode === 'original' ? '#06b6d4' : 'var(--text-muted)',
                        border: '1px solid var(--border-color)',
                        cursor: 'pointer',
                      }}
                    >
                      Original
                    </button>
                  </div>
                )}
              </div>

              {aiAnalysis && aiHeatmapUrl ? (
                <div>
                  {/* Heatmap Image View */}
                  <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                    <img
                      src={aiViewMode === 'heatmap' ? aiHeatmapUrl : aiImagePreview}
                      alt="AI Region Heatmap"
                      style={{ maxHeight: '200px', borderRadius: '8px', border: '1px solid var(--border-color)' }}
                    />
                  </div>

                  {/* Heatmap Color Legend */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px', fontSize: '11px', textAlign: 'center' }}>
                    <div style={{ padding: '6px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '6px', color: '#10b981', fontWeight: '700' }}>
                      Green: High Texture
                    </div>
                    <div style={{ padding: '6px', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '6px', color: '#f59e0b', fontWeight: '700' }}>
                      Amber: Medium
                    </div>
                    <div style={{ padding: '6px', background: 'rgba(14, 116, 144, 0.2)', border: '1px solid rgba(14, 116, 144, 0.4)', borderRadius: '6px', color: '#06b6d4', fontWeight: '700' }}>
                      Cyan: Smooth (Preserved)
                    </div>
                  </div>

                  {/* AI Class Distribution Breakdown */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '16px' }}>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>High Texture</span>
                      <p style={{ fontSize: '16px', fontWeight: '700', color: '#10b981' }}>
                        {aiAnalysis.high_texture_blocks} ({aiAnalysis.class_percentages.HighTexture}%)
                      </p>
                    </div>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Medium Texture</span>
                      <p style={{ fontSize: '16px', fontWeight: '700', color: '#f59e0b' }}>
                        {aiAnalysis.medium_texture_blocks} ({aiAnalysis.class_percentages.Medium}%)
                      </p>
                    </div>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Smooth (Untouched)</span>
                      <p style={{ fontSize: '16px', fontWeight: '700', color: '#06b6d4' }}>
                        {aiAnalysis.smooth_blocks} ({aiAnalysis.class_percentages.Smooth}%)
                      </p>
                    </div>
                  </div>

                  {/* Recommended Capacity Banner */}
                  <div style={{ padding: '12px 14px', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.25)', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>AI-Preserved Embedding Capacity</span>
                      <p style={{ fontSize: '15px', fontWeight: '800', color: '#fff' }}>
                        {aiAnalysis.recommended_capacity_bytes.toLocaleString()} Bytes ({((aiAnalysis.recommended_capacity_bytes / 1024)).toFixed(1)} KB)
                      </p>
                    </div>
                    <span style={{ fontSize: '11px', color: '#10b981', fontWeight: '600' }}>
                      Zero Smooth Modification
                    </span>
                  </div>

                  {/* Top 5 Ranked Blocks Table */}
                  {aiAnalysis.top_recommended_blocks && aiAnalysis.top_recommended_blocks.length > 0 && (
                    <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '12px' }}>
                      <span style={{ display: 'block', fontSize: '11px', fontWeight: '700', marginBottom: '8px', color: 'var(--text-muted)' }}>
                        Top AI-Ranked Embedding Blocks:
                      </span>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', textAlign: 'left' }}>
                          <thead>
                            <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}>
                              <th style={{ padding: '4px 6px' }}>Rank</th>
                              <th style={{ padding: '4px 6px' }}>Grid (X, Y)</th>
                              <th style={{ padding: '4px 6px' }}>Class</th>
                              <th style={{ padding: '4px 6px' }}>Suitability</th>
                              <th style={{ padding: '4px 6px' }}>P(High)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {aiAnalysis.top_recommended_blocks.slice(0, 5).map((blk, idx) => (
                              <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                <td style={{ padding: '4px 6px', fontWeight: '700', color: '#06b6d4' }}>#{idx + 1}</td>
                                <td style={{ padding: '4px 6px' }}>({blk.block_x}, {blk.block_y})</td>
                                <td style={{ padding: '4px 6px', color: blk.predicted_class === 2 ? '#10b981' : '#f59e0b' }}>{blk.class_name}</td>
                                <td style={{ padding: '4px 6px', fontWeight: '600' }}>{blk.suitability_score.toFixed(4)}</td>
                                <td style={{ padding: '4px 6px', color: '#10b981' }}>{(blk.prob_high_texture * 100).toFixed(1)}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                  <Sparkles size={40} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p style={{ fontSize: '14px' }}>Upload an image to inspect spatial block textures and generate AI heatmaps.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB: CNN STEGANALYZER (PHASE 16) */}
      {activeTab === 'steganalyzer' && (
        <div>
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
                  Deep Learning Steganalyzer CNN
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
                  Adversarial PyTorch CNN with Spatial Rich Model (SRM) High-Pass Filtering preprocessing. Computes micro-residual noise energy and estimates steganographic detectability score P(stego).
                </p>
              </div>
              <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '999px', background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.3)' }}>
                PyTorch 2.14 Neural Network Active
              </span>
            </div>
          </div>

          {/* Model Specs Banner */}
          <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Cpu size={26} color="#a855f7" />
              <div>
                <span style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>
                  Model: SteganalyzerCNN (4 Conv Blocks + AdaptiveAvgPool)
                </span>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Preprocessing: 5×5 SRM Filter Bank (KV, Laplacian, Edge) | Non-linear truncation T=3.0 | 249,580 parameters
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '14px', fontSize: '12px' }}>
              <span style={{ color: '#10b981', fontWeight: '600' }}>Test Accuracy: 91.67%</span>
              <span style={{ color: '#06b6d4', fontWeight: '600' }}>ROC-AUC: 0.9630</span>
              <span style={{ color: '#a855f7', fontWeight: '600' }}>Decision Cutoff: τ = {detectThreshold}</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px' }}>
            {/* Left Card: Input & Sensitivity Configuration */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Eye size={18} color="#a855f7" /> 1. Upload Image to Inspect
              </h3>

              <form onSubmit={handleDetectSubmit}>
                {/* Upload Dropzone */}
                <div style={{ marginBottom: '20px' }}>
                  <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '8px', color: 'var(--text-muted)' }}>
                    Candidate Image (Cover PNG or Stego PNG)
                  </span>
                  <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '10px', padding: '24px 16px', textAlign: 'center', cursor: 'pointer', background: 'rgba(0,0,0,0.2)' }}>
                    {detectPreview ? (
                      <div>
                        <img src={detectPreview} alt="Target Preview" style={{ maxHeight: '180px', margin: '0 auto 12px', borderRadius: '8px', border: '1px solid rgba(168, 85, 247, 0.4)' }} />
                        <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#fff' }}>
                          {detectFile ? detectFile.name : 'Image Loaded'}
                        </span>
                      </div>
                    ) : (
                      <div>
                        <Upload size={32} color="#a855f7" style={{ margin: '0 auto 8px', opacity: 0.8 }} />
                        <span style={{ display: 'block', fontSize: '13px', fontWeight: '600', marginBottom: '4px' }}>Click to select an image</span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>PNG or JPEG format supported</span>
                      </div>
                    )}
                    <input type="file" accept="image/png,image/jpeg" onChange={handleDetectFileChange} style={{ display: 'none' }} />
                  </label>
                </div>

                {/* Sensitivity Threshold Slider */}
                <div style={{ marginBottom: '24px', padding: '14px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: '600' }}>Adversarial Decision Threshold (τ)</span>
                    <span style={{ fontSize: '13px', fontWeight: '700', color: '#a855f7' }}>{detectThreshold.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.10"
                    max="0.80"
                    step="0.05"
                    value={detectThreshold}
                    onChange={(e) => setDetectThreshold(parseFloat(e.target.value))}
                    style={{ width: '100%', accentColor: '#a855f7' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    <span>0.10 (Highly Sensitive)</span>
                    <span style={{ color: '#06b6d4' }}>0.35 (Default Architecture)</span>
                    <span>0.80 (Permissive)</span>
                  </div>
                </div>

                {detectError && (
                  <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', borderRadius: '8px', color: '#fca5a5', fontSize: '12px', marginBottom: '16px' }}>
                    {detectError}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={!detectFile || detectLoading}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '8px',
                    border: 'none',
                    background: detectLoading ? 'rgba(168, 85, 247, 0.4)' : 'linear-gradient(135deg, #a855f7 0%, #06b6d4 100%)',
                    color: '#fff',
                    fontWeight: '700',
                    fontSize: '14px',
                    cursor: detectLoading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  {detectLoading ? (
                    <>
                      <RefreshCw size={16} className="spin" /> Running PyTorch Inference...
                    </>
                  ) : (
                    <>
                      <Eye size={16} /> Run PyTorch CNN Steganalysis
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Right Card: Adversarial Detection Report */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="#06b6d4" /> 2. Adversarial Detection Report
              </h3>

              {detectResult ? (
                <div>
                  {/* Verdict Badge */}
                  <div
                    style={{
                      padding: '16px',
                      borderRadius: '10px',
                      marginBottom: '20px',
                      background: detectResult.is_stego
                        ? 'rgba(239, 68, 68, 0.12)'
                        : 'rgba(16, 185, 129, 0.12)',
                      border: `1px solid ${detectResult.is_stego ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    {detectResult.is_stego ? (
                      <AlertTriangle size={28} color="#ef4444" />
                    ) : (
                      <CheckCircle2 size={28} color="#10b981" />
                    )}
                    <div>
                      <h4 style={{ fontSize: '15px', fontWeight: '800', color: detectResult.is_stego ? '#f87171' : '#34d399', marginBottom: '2px' }}>
                        {detectResult.is_stego ? 'FLAGGED: STEGO PAYLOAD DETECTED' : 'PASS: AUTHENTIC / SECURE COVER'}
                      </h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        P(stego) = {(detectResult.stego_probability * 100).toFixed(1)}% vs. Cutoff τ = {(detectResult.decision_threshold * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>

                  {/* Detectability Probability Gauge */}
                  <div style={{ marginBottom: '20px', padding: '14px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '600' }}>Adversarial Probability P(stego)</span>
                      <span style={{ fontWeight: '800', color: detectResult.stego_probability >= 0.35 ? '#f87171' : '#34d399' }}>
                        {(detectResult.stego_probability * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div style={{ position: 'relative', height: '10px', background: 'rgba(255,255,255,0.1)', borderRadius: '5px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(100, detectResult.stego_probability * 100)}%`,
                          background: detectResult.stego_probability >= 0.65
                            ? '#ef4444'
                            : detectResult.stego_probability >= 0.35
                              ? '#f59e0b'
                              : '#10b981',
                          borderRadius: '5px',
                          transition: 'width 0.4s ease',
                        }}
                      />
                    </div>
                  </div>

                  {/* 4-Stat Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '20px' }}>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>SRM Residual Energy</span>
                      <p style={{ fontSize: '15px', fontWeight: '700', color: '#06b6d4' }}>
                        {detectResult.residual_energy.toFixed(4)}
                      </p>
                    </div>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Classifier Confidence</span>
                      <p style={{ fontSize: '15px', fontWeight: '700', color: '#a855f7' }}>
                        {(detectResult.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Categorical Risk</span>
                      <p style={{ fontSize: '14px', fontWeight: '700', color: detectResult.risk_level === 'CRITICAL' ? '#ef4444' : detectResult.risk_level === 'HIGH' ? '#f59e0b' : '#10b981' }}>
                        {detectResult.risk_level}
                      </p>
                    </div>
                    <div style={{ padding: '10px 12px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Decision Threshold</span>
                      <p style={{ fontSize: '14px', fontWeight: '700', color: '#38bdf8' }}>
                        τ = {detectResult.decision_threshold}
                      </p>
                    </div>
                  </div>

                  {/* Recommendation Guidance Box */}
                  <div style={{ padding: '12px 14px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                      System Recommendation:
                    </span>
                    <p style={{ fontSize: '13px', color: '#fff', lineHeight: 1.4 }}>
                      {detectResult.recommendation}
                    </p>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                  <Eye size={40} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p style={{ fontSize: '14px' }}>Upload an image and run CNN steganalysis to evaluate adversarial detectability.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: QUALITY & BENCHMARKS WORKSPACE (PHASE 9) */}
      {activeTab === 'metrics' && (
        <div>
          <div style={{ marginBottom: '24px' }}>
            <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              Image Quality & Steganography Benchmarking
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
              Full-reference objective fidelity assessment comparing original Cover PNG vs. Stego PNG. Computes PSNR, SSIM (Wang et al. 2004), Mean Squared Error, and Bit Error Rate (BER).
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '24px', marginBottom: '32px' }}>
            {/* Left: Input Panels (Cover + Stego + Payloads) */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={18} color="#06b6d4" /> 1. Upload Test Image Pair
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                {/* Cover Dropzone */}
                <div>
                  <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: 'var(--text-muted)' }}>
                    Original Cover Image (PNG)
                  </span>
                  <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '10px', padding: '20px 12px', textAlign: 'center', cursor: 'pointer', background: 'rgba(0,0,0,0.15)' }}>
                    {metricCoverPreview ? (
                      <img src={metricCoverPreview} alt="Cover Preview" style={{ maxHeight: '100px', margin: '0 auto 8px', borderRadius: '6px' }} />
                    ) : (
                      <Upload size={24} color="var(--text-muted)" style={{ margin: '0 auto 8px' }} />
                    )}
                    <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {metricCoverFile ? metricCoverFile.name : 'Select Cover PNG'}
                    </span>
                    <input type="file" accept="image/png" onChange={handleMetricCoverChange} style={{ display: 'none' }} />
                  </label>
                </div>

                {/* Stego Dropzone */}
                <div>
                  <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: 'var(--text-muted)' }}>
                    Stego Candidate Image (PNG)
                  </span>
                  <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '10px', padding: '20px 12px', textAlign: 'center', cursor: 'pointer', background: 'rgba(0,0,0,0.15)' }}>
                    {metricStegoPreview ? (
                      <img src={metricStegoPreview} alt="Stego Preview" style={{ maxHeight: '100px', margin: '0 auto 8px', borderRadius: '6px' }} />
                    ) : (
                      <Upload size={24} color="var(--text-muted)" style={{ margin: '0 auto 8px' }} />
                    )}
                    <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {metricStegoFile ? metricStegoFile.name : 'Select Stego PNG'}
                    </span>
                    <input type="file" accept="image/png" onChange={handleMetricStegoChange} style={{ display: 'none' }} />
                  </label>
                </div>
              </div>

              {/* Optional Payloads for Bit Error Rate (BER) analysis */}
              <div style={{ marginBottom: '16px' }}>
                <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: 'var(--text-muted)' }}>
                  Original Message Payload (Optional — for BER Analysis)
                </span>
                <input
                  type="text"
                  placeholder="e.g. Secret Research Key 2026"
                  value={metricOrigText}
                  onChange={(e) => setMetricOrigText(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff', fontSize: '13px' }}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: 'var(--text-muted)' }}>
                  Recovered Message Payload (Optional)
                </span>
                <input
                  type="text"
                  placeholder="e.g. Secret Research Key 2026"
                  value={metricRecovText}
                  onChange={(e) => setMetricRecovText(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff', fontSize: '13px' }}
                />
              </div>

              {metricError && (
                <div style={{ padding: '10px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', color: '#f43f5e', fontSize: '13px', marginBottom: '16px' }}>
                  {metricError}
                </div>
              )}

              <button
                onClick={handleCompareMetricsSubmit}
                disabled={metricLoading || !metricCoverFile || !metricStegoFile}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  background: 'var(--gradient-cyber)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '14px',
                  opacity: metricLoading || !metricCoverFile || !metricStegoFile ? 0.6 : 1,
                  cursor: metricLoading || !metricCoverFile || !metricStegoFile ? 'not-allowed' : 'pointer',
                }}
              >
                {metricLoading ? <RefreshCw className="animate-spin" size={18} /> : <BarChart2 size={18} />}
                {metricLoading ? 'Computing Mathematical Quality Metrics...' : 'Compute Quality Metrics & Log Audit'}
              </button>
            </div>

            {/* Right: Metrics Results Cards */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BarChart2 size={18} color="#10b981" /> 2. Full-Reference Quality Report
              </h3>

              {metricResult ? (
                <div>
                  {/* Imperceptibility Header Banner */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    marginBottom: '20px',
                    background: metricResult.is_imperceptible ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                    border: `1px solid ${metricResult.is_imperceptible ? '#10b981' : '#f59e0b'}`,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Award size={22} color={metricResult.is_imperceptible ? '#10b981' : '#f59e0b'} />
                      <div>
                        <h4 style={{ fontSize: '14px', fontWeight: '700', color: metricResult.is_imperceptible ? '#10b981' : '#f59e0b' }}>
                          Rating: {metricResult.quality_rating}
                        </h4>
                        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          {metricResult.is_imperceptible
                            ? 'Imperceptible to Human Visual System (HVS)'
                            : 'Caution: Perceptible noise or modified structure detected'}
                        </p>
                      </div>
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: '700', padding: '4px 10px', borderRadius: '999px', background: 'rgba(0,0,0,0.3)', color: '#fff' }}>
                      {metricResult.width}×{metricResult.height}
                    </span>
                  </div>

                  {/* 4 Metrics Primary Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px', marginBottom: '20px' }}>
                    {/* PSNR Card */}
                    <div style={{ padding: '14px', background: 'rgba(0,0,0,0.25)', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Peak Signal-to-Noise Ratio</span>
                      <p style={{ fontSize: '22px', fontWeight: '800', color: '#38bdf8', margin: '4px 0 2px' }}>
                        {metricResult.is_psnr_infinite ? 'Infinity' : `${metricResult.psnr_db.toFixed(2)} dB`}
                      </p>
                      <span style={{ fontSize: '11px', color: metricResult.psnr_db >= 40 ? '#10b981' : '#f59e0b' }}>
                        {metricResult.psnr_db >= 50 ? '● Exceptional (> 50 dB)' : metricResult.psnr_db >= 40 ? '● High Quality (> 40 dB)' : '● Sub-40 dB'}
                      </span>
                    </div>

                    {/* SSIM Card */}
                    <div style={{ padding: '14px', background: 'rgba(0,0,0,0.25)', borderRadius: '10px', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Structural Similarity (SSIM)</span>
                      <p style={{ fontSize: '22px', fontWeight: '800', color: '#c084fc', margin: '4px 0 2px' }}>
                        {metricResult.ssim.toFixed(6)}
                      </p>
                      <span style={{ fontSize: '11px', color: '#a855f7' }}>
                        Wang et al. (2004) [Max: 1.0]
                      </span>
                    </div>

                    {/* MSE Card */}
                    <div style={{ padding: '14px', background: 'rgba(0,0,0,0.25)', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Mean Squared Error (MSE)</span>
                      <p style={{ fontSize: '22px', fontWeight: '800', color: '#34d399', margin: '4px 0 2px' }}>
                        {metricResult.mse.toFixed(6)}
                      </p>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        Per-pixel intensity variance
                      </span>
                    </div>

                    {/* Bit Error Rate (BER) Card */}
                    <div style={{ padding: '14px', background: 'rgba(0,0,0,0.25)', borderRadius: '10px', border: '1px solid rgba(251, 146, 60, 0.2)' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Bit Error Rate (BER)</span>
                      <p style={{ fontSize: '22px', fontWeight: '800', color: '#fb923c', margin: '4px 0 2px' }}>
                        {metricResult.payload_ber !== null ? `${(metricResult.payload_ber * 100).toFixed(2)}%` : '0.00%'}
                      </p>
                      <span style={{ fontSize: '11px', color: metricResult.payload_ber === 0 ? '#10b981' : '#f43f5e' }}>
                        Image LSB modified: {(metricResult.image_lsb_ber * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>

                  {/* Per-Channel Breakdown */}
                  {metricResult.ssim_channels && (
                    <div style={{ padding: '12px 14px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', fontSize: '12px' }}>
                      <span style={{ display: 'block', fontWeight: '600', marginBottom: '6px', color: 'var(--text-muted)' }}>
                        Per-Channel Structural Similarity:
                      </span>
                      <div style={{ display: 'flex', gap: '16px' }}>
                        <span style={{ color: '#ef4444' }}>Red: {metricResult.ssim_channels.R?.toFixed(6) || 'N/A'}</span>
                        <span style={{ color: '#22c55e' }}>Green: {metricResult.ssim_channels.G?.toFixed(6) || 'N/A'}</span>
                        <span style={{ color: '#3b82f6' }}>Blue: {metricResult.ssim_channels.B?.toFixed(6) || 'N/A'}</span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
                  <Activity size={40} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                  <p style={{ fontSize: '14px' }}>Upload Cover and Stego images and click compute to assess distortion.</p>
                </div>
              )}
            </div>
          </div>

          {/* Phase 14: 3-Way Empirical Comparative Studio */}
          <div className="glass-panel" style={{ padding: '24px', marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Sparkles size={22} color="#38bdf8" />
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: '700' }}>
                    Phase 14: 3-Way Empirical Benchmark (Baseline vs. Rule-Based vs. AI-Adaptive)
                  </h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Embeds the identical payload across all three algorithms on the exact same cover image to measure objective PSNR, SSIM, and MSE fidelity gains.
                  </p>
                </div>
              </div>
              <span style={{ fontSize: '11px', fontWeight: '700', padding: '4px 10px', borderRadius: '999px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
                Controlled 3-Way Study
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '20px' }}>
              <div>
                <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: 'var(--text-muted)' }}>
                  Cover Test Image (PNG)
                </span>
                <label style={{ display: 'block', border: '2px dashed var(--border-color)', borderRadius: '10px', padding: '16px', textAlign: 'center', cursor: 'pointer', background: 'rgba(0,0,0,0.15)' }}>
                  {compCoverPreview ? (
                    <img src={compCoverPreview} alt="Comp Cover" style={{ maxHeight: '90px', margin: '0 auto 8px', borderRadius: '6px' }} />
                  ) : (
                    <Upload size={22} color="var(--text-muted)" style={{ margin: '0 auto 6px' }} />
                  )}
                  <span style={{ display: 'block', fontSize: '12px', fontWeight: '600' }}>
                    {compCoverFile ? compCoverFile.name : 'Choose Cover PNG'}
                  </span>
                  <input type="file" accept="image/png" onChange={handleCompCoverChange} style={{ display: 'none' }} />
                </label>
              </div>

              <div>
                <span style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '6px', color: 'var(--text-muted)' }}>
                  Secret Benchmark Payload
                </span>
                <textarea
                  rows={4}
                  value={compMessage}
                  onChange={(e) => setCompMessage(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff', fontSize: '12px', resize: 'vertical' }}
                  placeholder="Enter secret text payload for comparison..."
                />
              </div>
            </div>

            {compError && (
              <div style={{ padding: '10px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', color: '#f43f5e', fontSize: '12px', marginBottom: '16px' }}>
                {compError}
              </div>
            )}

            <button
              onClick={handleCompSubmit}
              disabled={compLoading || !compCoverFile || !compMessage.trim()}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                width: '100%',
                padding: '12px',
                background: compLoading || !compCoverFile ? 'rgba(255,255,255,0.08)' : 'var(--gradient-cyber)',
                borderRadius: '8px',
                color: '#fff',
                fontWeight: '700',
                fontSize: '14px',
                cursor: compLoading || !compCoverFile ? 'not-allowed' : 'pointer',
                marginBottom: compResult ? '24px' : '0',
              }}
            >
              {compLoading ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} />}
              {compLoading ? 'Executing 3-Way Comparative Benchmark...' : 'Run 3-Way Comparative Benchmark Analysis'}
            </button>

            {/* Comparison Results Card */}
            {compResult && (
              <div style={{ marginTop: '20px' }}>
                {/* Improvement Banner */}
                <div style={{ padding: '14px 18px', background: 'rgba(56, 189, 248, 0.12)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '10px', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Award size={24} color="#38bdf8" />
                    <div>
                      <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#38bdf8' }}>
                        AI Random Forest Fidelity Superiority
                      </h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        Embedded payload size: {compResult.payload_bytes} bytes across all 3 methods
                      </p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '20px', textAlign: 'right' }}>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>PSNR vs Baseline:</span>
                      <p style={{ fontSize: '16px', fontWeight: '800', color: compResult.psnr_gain_vs_baseline_db >= 0 ? '#10b981' : '#38bdf8' }}>
                        {compResult.psnr_gain_vs_baseline_db >= 0 ? `+${compResult.psnr_gain_vs_baseline_db.toFixed(2)} dB` : `${compResult.psnr_gain_vs_baseline_db.toFixed(2)} dB`}
                      </p>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>PSNR vs Rule:</span>
                      <p style={{ fontSize: '16px', fontWeight: '800', color: compResult.psnr_gain_vs_rule_db >= 0 ? '#10b981' : '#38bdf8' }}>
                        {compResult.psnr_gain_vs_rule_db >= 0 ? `+${compResult.psnr_gain_vs_rule_db.toFixed(2)} dB` : `${compResult.psnr_gain_vs_rule_db.toFixed(2)} dB`}
                      </p>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>SSIM vs Baseline:</span>
                      <p style={{ fontSize: '16px', fontWeight: '800', color: compResult.ssim_gain_vs_baseline >= 0 ? '#10b981' : '#38bdf8' }}>
                        {compResult.ssim_gain_vs_baseline >= 0 ? `+${compResult.ssim_gain_vs_baseline.toFixed(6)}` : compResult.ssim_gain_vs_baseline.toFixed(6)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Side-by-Side 3-Card Comparison Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', marginBottom: '20px' }}>
                  {/* Card 1: Baseline LSB */}
                  <div style={{ padding: '16px', background: 'rgba(0,0,0,0.3)', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)' }}>
                        Baseline Sequential LSB
                      </span>
                      <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.1)' }}>
                        Phase 7
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '12px' }}>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>PSNR</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#38bdf8' }}>
                          {compResult.baseline_lsb.psnr_db.toFixed(2)} dB
                        </p>
                      </div>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>SSIM</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#a855f7' }}>
                          {compResult.baseline_lsb.ssim.toFixed(4)}
                        </p>
                      </div>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>MSE</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#f59e0b' }}>
                          {compResult.baseline_lsb.mse.toFixed(4)}
                        </p>
                      </div>
                    </div>

                    <p style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                      Altered pixels: {compResult.baseline_lsb.altered_pixels.toLocaleString()} px. Arbitrary raster scan alters smooth and flat pixels indiscriminately.
                    </p>
                  </div>

                  {/* Card 2: Rule-Based Adaptive LSB */}
                  <div style={{ padding: '16px', background: 'rgba(6, 182, 212, 0.05)', borderRadius: '10px', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: '#06b6d4' }}>
                        Rule-Based Adaptive
                      </span>
                      <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(6, 182, 212, 0.2)', color: '#06b6d4' }}>
                        Phase 10
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '12px' }}>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>PSNR</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#10b981' }}>
                          {compResult.rule_adaptive_lsb.psnr_db.toFixed(2)} dB
                        </p>
                      </div>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>SSIM</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#a855f7' }}>
                          {compResult.rule_adaptive_lsb.ssim.toFixed(4)}
                        </p>
                      </div>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>MSE</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#f59e0b' }}>
                          {compResult.rule_adaptive_lsb.mse.toFixed(4)}
                        </p>
                      </div>
                    </div>

                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                      <div>Blocks Used: <strong style={{ color: '#06b6d4' }}>{compResult.rule_adaptive_lsb.blocks_utilized}</strong></div>
                      <div>Smooth Untouched: <strong style={{ color: '#10b981' }}>{compResult.rule_adaptive_lsb.blocks_preserved_smooth}</strong></div>
                    </div>
                  </div>

                  {/* Card 3: AI Random Forest Adaptive LSB */}
                  <div style={{ padding: '16px', background: 'rgba(56, 189, 248, 0.08)', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.4)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: '#38bdf8' }}>
                        AI Random Forest LSB
                      </span>
                      <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(56, 189, 248, 0.25)', color: '#38bdf8', fontWeight: '700' }}>
                        Phase 14 (AI)
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '12px' }}>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>PSNR</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#38bdf8' }}>
                          {compResult.ai_adaptive_lsb.psnr_db.toFixed(2)} dB
                        </p>
                      </div>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>SSIM</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#a855f7' }}>
                          {compResult.ai_adaptive_lsb.ssim.toFixed(4)}
                        </p>
                      </div>
                      <div style={{ padding: '6px', background: 'rgba(255,255,255,0.03)', borderRadius: '6px' }}>
                        <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>MSE</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#f59e0b' }}>
                          {compResult.ai_adaptive_lsb.mse.toFixed(4)}
                        </p>
                      </div>
                    </div>

                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                      <div>Blocks Used: <strong style={{ color: '#38bdf8' }}>{compResult.ai_adaptive_lsb.blocks_utilized}</strong></div>
                      <div>Smooth Untouched: <strong style={{ color: '#10b981' }}>{compResult.ai_adaptive_lsb.blocks_preserved_smooth}</strong></div>
                    </div>
                  </div>
                </div>

                {/* Research Insight */}
                <div style={{ padding: '12px 14px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  <span style={{ fontWeight: '700', color: '#fff', display: 'block', marginBottom: '4px' }}>
                    Scientific Key Takeaway:
                  </span>
                  AI Random Forest dynamic classification optimizes HVS visual masking by predicting the highest-entropy spatial blocks using MSB-invariant features. Smooth regions are preserved 100% untouched, minimizing steganalytic residual anomalies while providing zero-overhead self-synchronizing extraction.
                </div>
              </div>
            )}
          </div>

          {/* Historical Research Experiment Audit Log Table */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <BarChart2 size={20} color="#06b6d4" />
                <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Research Benchmark Audit Log (CSV Records)</h3>
              </div>
              <button
                onClick={loadMetricsHistory}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-secondary)',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                <RefreshCw size={12} /> Refresh History
              </button>
            </div>

            {metricsHistory.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '8px 10px' }}>Timestamp</th>
                      <th style={{ padding: '8px 10px' }}>Method</th>
                      <th style={{ padding: '8px 10px' }}>Resolution</th>
                      <th style={{ padding: '8px 10px' }}>MSE</th>
                      <th style={{ padding: '8px 10px' }}>PSNR (dB)</th>
                      <th style={{ padding: '8px 10px' }}>SSIM</th>
                      <th style={{ padding: '8px 10px' }}>LSB Altered</th>
                      <th style={{ padding: '8px 10px' }}>Payload BER</th>
                      <th style={{ padding: '8px 10px' }}>Rating</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metricsHistory.map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ padding: '8px 10px', color: 'var(--text-muted)' }}>{new Date(row.timestamp).toLocaleTimeString()}</td>
                        <td style={{ padding: '8px 10px', fontWeight: '600', color: '#06b6d4' }}>{row.method}</td>
                        <td style={{ padding: '8px 10px' }}>{row.dimensions}</td>
                        <td style={{ padding: '8px 10px' }}>{row.mse}</td>
                        <td style={{ padding: '8px 10px', fontWeight: '700', color: parseFloat(row.psnr_db) >= 40 ? '#10b981' : '#f59e0b' }}>
                          {row.psnr_db} dB
                        </td>
                        <td style={{ padding: '8px 10px', fontWeight: '600', color: '#a855f7' }}>{row.ssim}</td>
                        <td style={{ padding: '8px 10px' }}>{(parseFloat(row.image_lsb_ber || 0) * 100).toFixed(2)}%</td>
                        <td style={{ padding: '8px 10px', color: parseFloat(row.payload_ber || 0) === 0 ? '#10b981' : '#f43f5e' }}>
                          {(parseFloat(row.payload_ber || 0) * 100).toFixed(2)}%
                        </td>
                        <td style={{ padding: '8px 10px' }}>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '999px',
                            fontSize: '10px',
                            fontWeight: '700',
                            background: row.quality_rating === 'EXCELLENT' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                            color: row.quality_rating === 'EXCELLENT' ? '#10b981' : '#f59e0b',
                          }}>
                            {row.quality_rating}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center', padding: '24px 0' }}>
                No empirical benchmarks logged yet. Encode an image or execute a comparison to populate audit history.
              </p>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: RSA KEY VAULT */}
      {activeTab === 'keys' && (
        <div>
          <div style={{ marginBottom: '24px' }}>
            <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              Cryptographic RSA Key Vault
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
              Your account's active RSA-4096 public key and fingerprint. Private keys are encrypted at rest with AES-256-GCM.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '28px', marginBottom: '24px' }}>
            {user ? (
              keyData ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <div>
                      <h3 style={{ fontSize: '16px', fontWeight: '700' }}>Active RSA-4096 Public Key</h3>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Created on {new Date(keyData.createdAt).toLocaleString()}</p>
                    </div>
                    <button
                      onClick={handleRegenerateKeys}
                      disabled={keyLoading}
                      style={{
                        padding: '8px 16px',
                        background: 'rgba(245, 158, 11, 0.15)',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        borderRadius: '8px',
                        color: '#f59e0b',
                        fontWeight: '600',
                        fontSize: '13px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <RefreshCw size={14} className={keyLoading ? 'animate-spin' : ''} />
                      Rotate / Regenerate Keys
                    </button>
                  </div>

                  <div style={{ padding: '12px 16px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      <strong>SHA-256 Fingerprint:</strong> <code style={{ color: '#06b6d4' }}>{keyData.keyFingerprint}</code>
                    </span>
                  </div>

                  <div style={{ position: 'relative' }}>
                    <textarea
                      readOnly
                      rows={8}
                      value={keyData.publicKeyPem}
                      style={{
                        width: '100%',
                        background: 'rgba(0,0,0,0.4)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '8px',
                        padding: '12px',
                        color: '#9ca3af',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '11px',
                      }}
                    />
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(keyData.publicKeyPem);
                        setCopiedKey(true);
                        setTimeout(() => setCopiedKey(false), 2000);
                      }}
                      style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        padding: '6px 12px',
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        color: '#fff',
                        fontSize: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      {copiedKey ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                      {copiedKey ? 'Copied' : 'Copy PEM'}
                    </button>
                  </div>

                  {/* Private Key Reveal & Export Section */}
                  <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <div>
                        <span style={{ fontSize: '14px', fontWeight: '700', color: '#f43f5e', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Lock size={15} /> RSA-4096 Private Key (Secret Decryption Key)
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Encrypted at rest with AES-256-GCM in SQL Server LocalDB. Decrypted on demand for decryption testing.</span>
                      </div>
                      <button
                        type="button"
                        onClick={handleTogglePrivateKey}
                        style={{ padding: '6px 14px', borderRadius: '6px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#f43f5e', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
                      >
                        {showVaultPrivateKey ? 'Hide Private Key' : 'Reveal Private Key'}
                      </button>
                    </div>

                    {showVaultPrivateKey && vaultPrivateKey && (
                      <div style={{ position: 'relative' }}>
                        <textarea
                          readOnly
                          rows={8}
                          value={vaultPrivateKey}
                          style={{
                            width: '100%',
                            background: 'rgba(0,0,0,0.4)',
                            border: '1px solid rgba(244, 63, 94, 0.3)',
                            borderRadius: '8px',
                            padding: '12px',
                            color: '#f43f5e',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '11px',
                          }}
                        />
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(vaultPrivateKey);
                            setCopiedPrivateKey(true);
                            setTimeout(() => setCopiedPrivateKey(false), 2000);
                          }}
                          style={{
                            position: 'absolute',
                            top: '10px',
                            right: '10px',
                            padding: '6px 12px',
                            background: 'rgba(255,255,255,0.1)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            color: '#fff',
                            fontSize: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                          }}
                        >
                          {copiedPrivateKey ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                          {copiedPrivateKey ? 'Copied' : 'Copy Private PEM'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '30px' }}>
                  <p>Loading active key metadata...</p>
                </div>
              )
            ) : (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Key size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
                <h4 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '6px' }}>Please Log In to Access Key Vault</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '16px' }}>
                  Cryptographic keys are tied to individual user credentials and encrypted at rest in SQL Server.
                </p>
                <button
                  onClick={() => setActiveTab('auth')}
                  style={{ padding: '8px 20px', borderRadius: '8px', background: 'var(--gradient-cyber)', color: '#fff', fontWeight: '600', fontSize: '13px' }}
                >
                  Go to Login
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: AUTHENTICATION / PROFILE */}
      {activeTab === 'auth' && (
        <div style={{ maxWidth: '480px', width: '100%', margin: '0 auto' }}>
          <div className="glass-panel" style={{ padding: '32px' }}>
            {user ? (
              <div>
                <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                  <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--gradient-cyber)', margin: '0 auto 12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <User size={32} color="#fff" />
                  </div>
                  <h2 style={{ fontSize: '20px', fontWeight: '800' }}>{user.username}</h2>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{user.email}</span>
                </div>

                <div style={{ padding: '16px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', marginBottom: '20px', fontSize: '13px' }}>
                  <p style={{ marginBottom: '8px' }}><strong>User ID:</strong> <code style={{ fontSize: '11px', wordBreak: 'break-all' }}>{user.userId}</code></p>
                  <p style={{ color: '#10b981' }}><strong>Status:</strong> Active Authenticated Session</p>
                </div>

                <button
                  onClick={handleLogout}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '8px',
                    background: 'rgba(244, 63, 94, 0.15)',
                    border: '1px solid rgba(244, 63, 94, 0.3)',
                    color: '#f43f5e',
                    fontWeight: '700',
                    fontSize: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  <LogOut size={16} /> Log Out
                </button>
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', background: 'rgba(0,0,0,0.25)', padding: '4px', borderRadius: '8px' }}>
                  <button
                    onClick={() => setAuthMode('login')}
                    style={{ flex: 1, padding: '8px', borderRadius: '6px', fontWeight: '600', fontSize: '13px', color: authMode === 'login' ? '#fff' : 'var(--text-muted)', background: authMode === 'login' ? 'var(--gradient-cyber)' : 'transparent' }}
                  >
                    Login
                  </button>
                  <button
                    onClick={() => setAuthMode('register')}
                    style={{ flex: 1, padding: '8px', borderRadius: '6px', fontWeight: '600', fontSize: '13px', color: authMode === 'register' ? '#fff' : 'var(--text-muted)', background: authMode === 'register' ? 'var(--gradient-cyber)' : 'transparent' }}
                  >
                    Register
                  </button>
                </div>

                <form onSubmit={handleAuthSubmit}>
                  {authMode === 'register' && (
                    <div style={{ marginBottom: '16px' }}>
                      <label style={{ display: 'block', fontSize: '13px', marginBottom: '6px', fontWeight: '500' }}>Username</label>
                      <input
                        type="text"
                        required
                        value={authForm.username}
                        onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
                        style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff' }}
                      />
                    </div>
                  )}

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', marginBottom: '6px', fontWeight: '500' }}>Email Address</label>
                    <input
                      type="email"
                      required
                      value={authForm.email}
                      onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                      style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff' }}
                    />
                  </div>

                  <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', fontSize: '13px', marginBottom: '6px', fontWeight: '500' }}>Password</label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showAuthPassword ? 'text' : 'password'}
                        required
                        minLength={8}
                        value={authForm.password}
                        onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                        style={{ width: '100%', padding: '10px 40px 10px 14px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff' }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowAuthPassword(!showAuthPassword)}
                        style={{
                          position: 'absolute',
                          right: '10px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          background: 'transparent',
                          color: 'var(--text-muted)',
                          padding: '4px',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        {showAuthPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>

                  {authError && (
                    <div style={{ padding: '10px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '8px', color: '#f43f5e', fontSize: '13px', marginBottom: '16px' }}>
                      {authError}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={authLoading}
                    style={{
                      width: '100%',
                      padding: '12px',
                      borderRadius: '8px',
                      background: 'var(--gradient-cyber)',
                      color: '#fff',
                      fontWeight: '700',
                      fontSize: '14px',
                    }}
                  >
                    {authLoading ? 'Authenticating...' : authMode === 'login' ? 'Sign In' : 'Create Account'}
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: ARCHITECTURE & SYSTEM STATS */}
      {activeTab === 'dashboard' && (
        <div>
          <div style={{ marginBottom: '24px' }}>
            <h1 style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              System Architecture & Health Monitor
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
              Overview of the multi-tier research architecture and operational statuses.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '32px' }}>
            {/* React Frontend Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Terminal size={20} color="#3b82f6" />
                  <h3 style={{ fontSize: '16px', fontWeight: '600' }}>React Frontend</h3>
                </div>
                <span style={{ fontSize: '11px', fontWeight: '700', color: '#10b981', background: 'rgba(16, 185, 129, 0.15)', padding: '3px 8px', borderRadius: '999px' }}>ACTIVE</span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Vite + React interactive UI with capacity meter and key vault.</p>
            </div>

            {/* ASP.NET Core Backend Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Server size={20} color="#6366f1" />
                  <h3 style={{ fontSize: '16px', fontWeight: '600' }}>ASP.NET Core Web API</h3>
                </div>
                <span style={{ fontSize: '11px', fontWeight: '700', color: aspNetStatus === 'healthy' ? '#10b981' : '#f59e0b', background: aspNetStatus === 'healthy' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)', padding: '3px 8px', borderRadius: '999px' }}>
                  {aspNetStatus.toUpperCase()}
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Identity, JWT authentication, RSA-4096 Key Vault & SQL Server persistence.</p>
            </div>

            {/* FastAPI AI Engine Card */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Cpu size={20} color="#06b6d4" />
                  <h3 style={{ fontSize: '16px', fontWeight: '600' }}>FastAPI AI Engine</h3>
                </div>
                <span style={{ fontSize: '11px', fontWeight: '700', color: fastApiStatus === 'healthy' ? '#10b981' : '#f59e0b', background: fastApiStatus === 'healthy' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)', padding: '3px 8px', borderRadius: '999px' }}>
                  {fastApiStatus.toUpperCase()}
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>AES-256-GCM, RSA-OAEP, LSB steganography, capacity calculations & AI models.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
