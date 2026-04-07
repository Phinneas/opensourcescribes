# Audio Generation Setup Guide

## Overview

The OpenSourceScribes video generation system now uses a multi-tiered voice generation approach:

1. **Primary**: Minimax TTS (using video generation tokens)
2. **Backup**: Hume.ai (existing service)
3. **Backup**: OpenAI TTS
4. **Free Fallback**: KittenTTS (self-hosted)
5. **Built-in Fallback**: gTTS

## Configuration

### Minimax Setup (Primary)

Minimax now serves as the primary TTS service, leveraging your existing video generation tokens.

1. Get your Minimax API credentials:
   - API Key: From [Minimax Console](https://platform.minimaxi.com/user-center/basic-information)
   - Group ID: From your account settings

2. Update `config.json` or `config_enhanced.json`:
```json
{
  "minimax": {
    "api_key": "YOUR_MINIMAX_API_KEY",
    "group_id": "YOUR_MINIMAX_GROUP_ID"
  },
  "voice": {
    "minimax_voice_id": "male-1",
    "minimax_speed": 1.0,
    "minimax_model": "speech-01"
  }
}
```

**Available Minimax Voices:**
- `male-1`: Male voice (deeper)
- `male-2`: Male voice (lighter)
- `female-1`: Female voice (warm)
- `female-2`: Female voice (crisp)

**Speed Range:** 0.5 to 2.0 (1.0 is normal)

### KittenTTS Setup (Free Fallback)

KittenTTS is a free, self-hosted TTS system that serves as our primary fallback.

1. **Installation:**
```bash
pip install kittentts
```

2. **Start the server:**
```bash
# Default port is 5000
kittentts-server --host 0.0.0.0 --port 5000
```

Or with Docker:
```bash
docker run -p 5000:5000 kittentts/kittentts:latest
```

3. **Verify it's running:**
```bash
curl http://localhost:5000/health
# Should return: {"status": "healthy"}
```

4. **Configuration (already in config files):**
```json
{
  "kittentts": {
    "enabled": true,
    "base_url": "http://localhost:5000",
    "auto_start": false
  },
  "voice": {
    "kittentts_model": "kit/ljspeech-tts",
    "kittentts_speed": 1.0
  }
}
```

**Available KittenTTS Models:**
- `kit/ljspeech-tts`: Default English TTS (good quality)
- `kit/vctk-tts`: Multi-speaker English TTS
- `kit/thorsten-tts`: German TTS
- `kit/kokoro-tts`: Alternative English TTS

### Hume.ai Setup (Existing)

Hume.ai remains as a backup service and should already be configured.

```json
{
  "hume_ai": {
    "api_key": "YOUR_HUME_API_KEY",
    "secret_key": "YOUR_HUME_SECRET_KEY",
    "enhanced_voice_id": "drew"
  },
  "voice": {
    "hume_voice_id": "drew",
    "hume_speed": 1.0
  }
}
```

**Available Hume Voices:**
- `drew`: Deep male voice (current default)
- `lily`: Warm female voice
- `anya`: Professional female voice

### OpenAI TTS Setup (Backup)

OpenAI provides another paid backup option.

```json
{
  "openai": {
    "api_key": "YOUR_OPENAI_API_KEY"
  },
  "voice": {
    "openai_voice": "nova",
    "openai_model": "tts-1-hd"
  }
}
```

**Available OpenAI Voices:**
- `alloy`: Neutral, professional
- `echo`: Male, deep
- `fable`: British accent
- `onyx`: Male, very deep
- `nova`: Female, friendly (default)
- `shimmer`: Female, bright

## Fallback Chain Behavior

The system will try services in this order:

1. **Minimax** (Primary)
   - Uses your existing video token balance
   - Highest priority for best quality
   
2. **Hume.ai** (Backup #1)
   - Existing service, reliable
   - Good quality, moderate cost
   
3. **OpenAI TTS** (Backup #2)
   - Good quality, lower cost
   - Requires OpenAI API key
   
4. **KittenTTS** (Free Fallback)
   - Self-hosted, completely free
   - Good quality for a free solution
   - Must be running locally
   
5. **gTTS** (Built-in Emergency Fallback)
   - Always available, completely free
   - Basic quality, robotic voice
   - Last resort to ensure audio generation always succeeds

## Testing Your Setup

Run the test script to verify your configuration:

```bash
python enhanced_audio_generator.py
```

Expected output:
```
============================================================
ENHANCED VOICE GENERATOR TEST
============================================================

Test text: Welcome back to OpenSourceScribes!...

============================================================
Testing voice generation services...
============================================================

🎙️ Attempting MINIMAX...
🎙️ Minimax TTS: Welcome back to OpenSourceScribes!...
   ✅ Minimax TTS generated (voice: male-1, speed: 1.0x)
   ✂️  Silence trimmed

✅ SUCCESS! Audio generated: test_enhanced_voice.mp3
```

If Minimax fails, you should see it gracefully fall back through the chain:

```
🎙️ Attempting MINIMAX...
   ⚠️  Minimax failed, trying next...

🎙️ Attempting HUME...
🎙️ Hume.ai: Welcome back to OpenSourceScribes!...
   ✅ Hume.ai voice generated (voice: drew, speed: 1.0x)
   ✂️  Silence trimmed

✅ SUCCESS! Audio generated: test_enhanced_voice.mp3
```

## Troubleshooting

### Minimax Issues

**Problem**: "Minimax API credentials not configured"
- **Solution**: Add your Minimax API key and group ID to config.json

**Problem**: "Minimax API error: 401"
- **Solution**: Check your API key is correct and has sufficient balance

**Problem**: "Minimax API error: 429"
- **Solution**: Rate limited - wait a moment and retry, or check token balance

### KittenTTS Issues

**Problem**: "KittenTTS not available at http://localhost:5000"
- **Solution**: Start the KittenTTS server:
  ```bash
  pip install kittentts
  kittentts-server
  ```

**Problem**: "Connection refused"
- **Solution**: Ensure the server is running and accessible:
  ```bash
  curl http://localhost:5000/health
  ```

### General Issues

**Problem**: Audio files are silent or have long pauses
- **Solution**: Check `enhanced_audio_generator.py` line 397 - silence trimming is automatic

**Problem**: "All voice services failed!"
- **Solution**: Check internet connection and all API credentials. gTTS should always work as final fallback.

## Cost Comparison

| Service | Cost per Minute | Quality | Speed | Notes |
|---------|-----------------|---------|-------|-------|
| **Minimax** | Uses video tokens | ⭐⭐⭐⭐⭐ | Fast | Uses existing token balance |
| Hume.ai | ~$0.20 | ⭐⭐⭐⭐ | Fast | Current backup |
| OpenAI TTS | ~$0.15 | ⭐⭐⭐⭐ | Fast | Good value backup |
| KittenTTS | **FREE** | ⭐⭐⭐ | Medium | Self-hosted |
| gTTS | **FREE** | ⭐⭐ | Fast | Built-in last resort |
| ~ElevenLabs~ | ~$0.30 | ⭐⭐⭐⭐⭐ | Fast | ~Deprecated but kept in code~ |

## Customization

### Change Default Voice

Edit your config file:
```json
{
  "voice": {
    "minimax_voice_id": "female-1",
    "hume_voice_id": "lily",
    "openai_voice": "alloy"
  }
}
```

### Adjust Speech Speed

```json
{
  "voice": {
    "minimax_speed": 1.2,
    "hume_speed": 0.9,
    "kittentts_speed": 1.1
  }
}
```

### Modify Fallback Chain

```json
{
  "voice": {
    "fallback_chain": ["minimax", "kittentts", "gtts"]
  }
}
```

## Migration from ElevenLabs

If you were previously using ElevenLabs:

1. **No code changes needed** - ElevenLabs is deprecated but still works if manually specified
2. **Update config**: The default `fallback_chain` now starts with Minimax
3. **Set credentials**: Add Minimax credentials to your config
4. **Test**: Run `python enhanced_audio_generator.py` to verify

Your existing ElevenLabs configuration remains in the file for potential future use.

## API Reference

### Minimax TTS API

- **Docs**: https://platform.minimaxi.com/document/introduction
- **Endpoint**: `POST /v1/text_to_speech?GroupId={group_id}`
- **Auth**: Bearer token + Group ID
- **Models**: `speech-01`, `speech-02` (premium)
- **Voices**: `male-1`, `male-2`, `female-1`, `female-2`

### KittenTTS API

- **Repo**: https://github.com/KittenML/KittenTTS
- **Endpoint**: `POST /tts`
- **Models**: Multiple pre-trained TTS models
- **Format**: Returns MP3 audio
- **No API Key**: Self-hosted, completely free

---

**Last Updated**: 2025-01-07  
**Current Default Chain**: `minimax → hume → openai → kittentts → gtts`  
**Status**: Minimax primary with robust free fallback options
