# Sacred Texts LLM Interface

**Goal**: Build an AI interface to query wisdom from sacred texts.

**Status**: Phase 1 complete ✅ | Phase 2 next 🚧

## Quick Start

```bash
./download_sacred_texts.py
```

Downloads 353 sacred texts (~5GB) from [sacred-texts.com](https://sacred-texts.com/download.htm).

## Next Steps
1. Text processing & chunking
2. Generate embeddings
3. Build RAG interface

---

## Notes for Agent

### Project Phases
**Phase 1: Data Collection** ✅ COMPLETE
- Created downloader for sacred-texts.com archive
- 353 texts covering all major spiritual traditions
- ~4-5GB total data with organized structure
- Tested and verified download scripts

**Phase 2: RAG Implementation** 🚧 NEXT
- Text processing and chunking
- Embedding generation 
- Vector database setup
- Search interface development

**Phase 3: Chat Interface** 📋 PLANNED
- Natural language query processing
- Context-aware responses
- Multi-tradition knowledge synthesis

### Data Sources
- **Primary**: [sacred-texts.com/download.htm](https://sacred-texts.com/download.htm)
- **Alternative**: [Google Drive backup](https://drive.google.com/drive/u/0/folders/1VYTr5l7jARi_Kb_aB0Jjjq2RZF9kacK7)

### Technical Details
- **Archive Size**: ~4-5 GB raw texts
- **RAG Storage**: ~15-20 GB (with embeddings/indexes)
- **File Count**: 353 texts (.txt.gz format)
- **Download Time**: 30-60 minutes
- **Structure**: Maintains sacred-texts.com hierarchy by tradition

### Collections Included
- **Buddhism**: 22 files (Jataka, Dhammapada, etc.)
- **Hinduism**: 23 files (Upanishads, Bhagavad Gita, etc.)
- **Christianity**: 25 files (Augustine, Aquinas, mystical texts)
- **Islam**: 15 files (Quran translations, Sufi poetry)
- **Judaism**: 9 files (Talmud, Kabbalah, Maimonides)
- **Taoism**: 6 files (Tao Te Ching, Art of War)
- **Celtic/Norse**: 64 files (Mabinogion, Poetic Edda)
- **Native American**: 13 files (Creation myths, tribal wisdom)
- **Esoteric**: 16 files (Hermetic texts, Gnostic gospels)
- **Other traditions**: 35+ categories

### Download Script Features
- Progress tracking with resume capability
- User-Agent handling to avoid 403 errors
- Maintains original directory structure
- Automatic extraction option
- Detailed logging and error reporting
- Creates collection metadata

### File Organization
```
sacred_texts_archive/
├── afr/          # African traditions
├── bud/          # Buddhism  
├── chr/          # Christianity
├── hin/          # Hinduism
├── isl/          # Islam
├── jud/          # Judaism
├── tao/          # Taoism
├── neu/          # European/Norse
├── nam/          # Native American
├── eso/          # Esoteric/Occult
└── extracted/    # Uncompressed texts
```

### Testing Completed
- ✅ URL accessibility verified
- ✅ Download functionality tested
- ✅ Content verification (extracted Lao Tzu text)
- ✅ Complete catalog validation (353 files = 100% coverage)
- ✅ User-Agent fix applied for 403 errors
- ✅ Directory structure maintenance confirmed
