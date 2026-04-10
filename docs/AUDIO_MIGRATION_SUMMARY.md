# Audio System Migration Summary

## Changes Made

### 1. Enhanced Audio Generator (`enhanced_audio_generator.py`)

#### Added
- **`generate_audio_minimax()`**: New primary TTS service using Minimax video tokens
  - Supports male/female voices (male-1, male-2, female-1, female-2)
  - Configurable speed (0.5-2.0x)
  - Direct API integration
  
- **`generate_audio_kittentts()`**: Free fallback TTS service
  - Self-hosted, no API costs
  - Multiple model support (LJSpeech, VCTK, etc.)
  - Requires local server running
  
- **`_make_api_request()`**: Helper for consistent API error handling

#### Modified
- **`generate_audio()`**: Updated fallback chain
  - OLD: `elevenlabs → hume → openai → cartes → gtts`
  - NEW: `minimax → hume → openai → kittentts → gtts`
  
- **ElevenLabs deprecated**: Kept in codebase but marked as deprecated
  - Shows warning when attempted
  - Not included in default fallback chain
  - Available for manual use if needed

#### Removed
- Nothing removed (ElevenLabs code kept for future use)

### 2. Configuration Files

#### `config.json` (Production Config)
**Added:**
```json
{
  "minimax": {
    "api_key": "YOUR_MINIMAX_API_KEY_HERE",
    "group_id": "YOUR_MINIMAX_GROUP_ID_HERE"
  },
  "voice": {
    "primary_service": "minimax",
    "fallback_chain": ["minimax", "hume", "openai", "kittentts", "gtts"],
    "minimax_voice_id": "male-1",
    "minimax_speed": 1.0,
    "kittentts_model": "kit/ljspeech-tts"
  }
}
```

#### `config_enhanced.json` (Enhanced Config)
**Updated:**
- Voice section now includes Minimax and KittenTTS settings
- Added complete Minimax configuration section
- Added KittenTTS configuration section
- ElevenLabs marked with `"status": "deprecated"`

### 3. New Documentation

#### `AUDIO_SETUP_GUIDE.md` (New)
Comprehensive setup guide covering:
- Minimax TTS setup and configuration
- KittenTTS installation and server setup (pip + Docker)
- Hume.ai and OpenAI TTS configuration
- Fallback chain behavior explanation
- Troubleshooting section
- Cost comparison table
- Testing and verification steps
- API reference

#### `test_audio_setup.py` (New)
Verification script that:
- Tests complete fallback chain
- Reports which services are configured
- Shows current fallback chain order
- Plays generated audio (platform-specific)
- Provides setup recommendations
- File size reporting

## Fallback Chain Priority

1. **Minimax** (NEW PRIMARY)
   - Uses existing video generation tokens
   - High quality, consistent performance
   - First in fallback chain

2. **Hume.ai** (Existing)
   - Kept as reliable backup
   - Good quality, ~$0.20/min
   - Second in fallback chain

3. **OpenAI TTS** (Existing)
   - Good quality, ~$0.15/min
   - Best value paid option
   - Third in fallback chain

4. **KittenTTS** (NEW FREE FALLBACK)
   - Self-hosted, completely free
   - Good quality for free solution
   - Fourth in fallback chain
   - Requires local server

5. **gTTS** (Existing)
   - Always available emergency fallback
   - Basic robotic quality
   - Last resort

## Migration Path

### For Existing Users

1. **Add Minimax Credentials**
   ```json
   {
     "minimax": {
       "api_key": "your_key_here",
       "group_id": "your_group_here"
     }
   }
   ```

2. **(Optional) Set up KittenTTS**
   ```bash
   pip install kittentts
   kittentts-server
   ```

3. **Run Test**
   ```bash
   python test_audio_setup.py
   ```

4. **No Code Changes Needed**
   - Existing code continues to work
   - Automatic Minimax priority
   - Graceful fallback if Minimax fails

### Service Status

| Service | Status | Priority | Cost | Notes |
|---------|--------|----------|------|-------|
| Minimax | ✅ Active | 1st | Uses video tokens | New primary |
| Hume.ai | ✅ Active | 2nd | ~$0.20/min | Existing backup |
| OpenAI | ✅ Active | 3rd | ~$0.15/min | Good value backup |
| KittenTTS | ✅ Active | 4th | **FREE** | Self-hosted |
| gTTS | ✅ Active | 5th | **FREE** | Emergency fallback |
| ElevenLabs | ⚠️ Deprecated | Manual only | ~$0.30/min | Kept in code |

## API Implementation Notes

### Minimax TTS API
- **Endpoint**: `POST /v1/text_to_speech?GroupId={group_id}`
- **Auth**: Bearer token + Group ID (both required)
- **Payload**: JSON with text, voice_id, speed, audio settings
- **Response**: Raw MP3 audio bytes
- **Voice IDs**: male-1, male-2, female-1, female-2
- **Speed Range**: 0.5 to 2.0 (1.0 is normal)
- **Models**: speech-01, speech-02

### KittenTTS API
- **Endpoint**: `POST /tts` (local server)
- **Default**: http://localhost:5000
- **Payload**: JSON with text, model, speed
- **Models**: kit/ljspeech-tts, kit/vctk-tts, etc.
- **No Authentication**: Self-hosted
- **Health Check**: GET /health

### Error Handling
- All API calls wrapped in try/except
- Timeout handling (30 seconds default)
- Connection error handling
- Graceful degradation through fallback chain
- Clear error messages for debugging

## Key Benefits

1. **Cost Savings**: Uses existing Minimax video tokens instead of paying for ElevenLabs
2. **Reliability**: 5-tier fallback ensures audio always generates
3. **Flexibility**: Easy to add/remove services via config
4. **Free Option**: KittenTTS provides quality free alternative
5. **Future-Proof**: ElevenLabs code kept if needed later
6. **Self-Hosted**: KittenTTS runs locally, no API dependencies

## Testing

Run verification:
```bash
python test_audio_setup.py
```

Expected output shows:
- ✅ Minimax: Configured (or ⚠️ needs setup)
- ✅ Hume.ai: Configured (or ⚠️ needs setup)
- ✅ OpenAI: Configured (or ⚠️ needs setup)
- ✅ KittenTTS: Available (or ⚠️ needs server)
- Generated test audio file
- Fallback chain order

## Configuration Files Changed

1. ✅ `enhanced_audio_generator.py` - Core logic updated
2. ✅ `config.json` - Added Minimax + voice settings
3. ✅ `config_enhanced.json` - Complete config structure
4. ✅ `AUDIO_SETUP_GUIDE.md` - NEW comprehensive guide
5. ✅ `test_audio_setup.py` - NEW verification script
6. ✅ `AUDIO_MIGRATION_SUMMARY.md` - This file

## Next Steps

1. **Get Minimax API credentials** if you don't have them
2. **Optional**: Set up KittenTTS for free fallback
3. **Run test**: `python test_audio_setup.py`
4. **Generate video**: Your existing `run_pipeline.py` will use new chain automatically

No changes needed to existing pipeline code - the new audio system is fully backward compatible!
