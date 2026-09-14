# 제작 소스 안내

Python 3.13, Pillow, Windows의 `C:/Windows/Fonts/gulim.ttc`를 사용한 작업 소스입니다. 원본 ROM은 README에 지정된 이름으로 저장소 루트에 별도 준비합니다.

1. `python ao2/tools/build_font_prototype.py`
2. `python ao2/tools/build_ui_stage.py`

두 번째 단계 결과는 `ao2/build/ui_stage/Albert Odyssey 2 - UI STAGE - NOT RELEASE.sfc`입니다. 역사적인 파일명으로, v06 통합 빌드 결과입니다. `build_release.py`는 작업 폴더의 구버전 ROM 보존 검사와 기존 검수 산출물까지 요구하는 내부 배포 도구이므로 공개 저장소만으로 바로 실행되지 않습니다. 먼저 개별 `verify_*.py` 검사들을 실행하고 결과를 검토해야 합니다.

런타임 검사에는 별도 Snes9x libretro DLL을 `analysis_font_scan/libretro/snes9x_libretro.dll`에 준비해야 합니다. 일부 검사 도구는 기존 로컬 시험 산출물·경로를 전제로 하므로 환경에 맞게 설정해야 합니다. 바이너리·세이브·추출 자원은 배포하지 않으며 필요한 자료는 원본에서 추출 도구로 생성하세요. 공개 시점에는 패치 적용 왕복 검증을 수행했으며, 공개 폴더에서 소스 전체를 재빌드한 검증은 하지 않았습니다.
