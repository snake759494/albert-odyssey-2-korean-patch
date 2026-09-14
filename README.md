# 알버트 오딧세이 2 한글패치

슈퍼패미컴 일본판 알버트 오딧세이 2용 비공식 한국어 패치입니다. 전투와 이야기를 진행하는 RPG의 대사와 화면 정보를 한국어로 표시합니다. 현재 배포 버전은 **v0.6**입니다.

[최신 패치 다운로드](https://github.com/snake759494/albert-odyssey-2-korean-patch/releases/latest) · [제작 소스 안내](docs/BUILD.md) · [수정 내역과 실제 플레이 검수](ao2/build/release_v06/수정내역과_실제플레이검수.md)

대사·메뉴·아이템 한글화 v06입니다. 지형 50종, 기술 18종, 상태 표시, 장비·도구 안내와 명중률 기호를 수정했습니다. 대사 2,131개의 CPU 처리·반환 및 메모리 경계를 검사했고, 새 게임 오프닝부터 첫 전투, 기술 사용·공격·장비·도구 메뉴·적의 턴을 실제 입력으로 확인했습니다.

## 배포 구성

스타오션 1 프로젝트와 같은 구성으로 제작 소스·번역·검수 자료를 공개합니다. 릴리즈 직접 첨부 파일은 **`Albert.Odyssey.2.-.Korean.Full.v06.xdelta` 하나**입니다. 원본·완성 ROM, 추출 바이너리·게임 글꼴 덤프·에뮬레이터·세이브 스테이트는 포함하지 않습니다. 자동 Source code ZIP/TAR는 공개 저장소 압축본입니다.

## 대상 원본과 확인값

수정되지 않은 일본판 `Albert Odyssey 2 Jashin no Taidou.smc`에 적용하세요. 파일명보다 크기와 해시가 중요합니다. 복사기 헤더를 추가한 파일이나 이전 한글판에 덧씌우면 안 됩니다. 원본은 별도로 준비해야 합니다.

| 항목 | 값 |
| --- | --- |
| 원본 크기 | `2097152` |
| 원본 MD5 | `17ee32db6de1524535d2f2e995380f70` |
| 원본 SHA-256 | `7c6fe76fe1a414407435c7393f4d9b50a885fa6055cd9d94549725884497698b` |
| xdelta 크기 | `104933` |
| xdelta MD5 | `79702743b11d687dda217f5e56df71c7` |
| xdelta SHA-256 | `3603f4843c4d3d90ebf173a8577c6dc1ae561369dd02779075fe5b8d2b9001ef` |
| 결과 ROM 크기 | `4194304` |
| 결과 ROM MD5 | `68aa472e79d95a9665707638406c686a` |
| 결과 ROM SHA-256 | `0b00d3e6dc2f20bb9602ad359a6ba44780cdacbe1a89b846ecf576eb84776ac5` |


## 적용 방법

1. 위 원본의 MD5와 SHA-256을 확인합니다. PowerShell: `Get-FileHash -Algorithm SHA256 -LiteralPath './Albert Odyssey 2 Jashin no Taidou.smc'` (MD5는 알고리즘을 MD5로 변경).
2. xdelta3 지원 도구의 Apply Patch에서 Patch는 다운로드한 xdelta, Source는 원본 ROM으로 지정합니다.
3. Output은 원본과 다른 새 파일명으로 지정합니다.
4. 결과 SHA-256을 위 표와 비교합니다.
5. 게임을 완전히 종료하고 새 ROM을 여세요. 이전 버전의 에뮬레이터 강제 저장은 옛 코드·글꼴을 복원할 수 있으므로 게임 내 일반 저장으로 이어 하세요.

```powershell
.\xdelta3.exe -d -s './Albert Odyssey 2 Jashin no Taidou.smc' './Albert.Odyssey.2.-.Korean.Full.v06.xdelta' './Albert Odyssey 2 - Korean Full v06.sfc'
python tools/apply_release.py --xdelta './xdelta3.exe' --source './Albert Odyssey 2 Jashin no Taidou.smc' --patch './Albert.Odyssey.2.-.Korean.Full.v06.xdelta' --output './new-korean.sfc'
```

두 명령은 대안입니다. 자체 적용 도구는 원본·패치·결과 해시를 검사하고 기존 출력 파일을 덮어쓰지 않습니다. xdelta 도구는 별도 준비하며 이 배포에 실행 파일은 포함하지 않습니다.

## 검증 범위와 제보

원본에 배포 xdelta를 적용한 결과가 완성 ROM과 바이트 단위로 일치함을 재확인했습니다. 상세한 검사 조건은 위 검수 기록을 참고하세요. **모든 분기·엔딩까지 완주한 검증이나 실제 슈퍼패미컴 기기 검증은 아닙니다.** 보고된 검사 수치는 모든 진행 상황에서 무오류라는 뜻이 아닙니다.

제보에는 버전, 결과 ROM SHA-256, 에뮬레이터 버전, 장소와 재현 순서, 강제 저장 사용 여부를 적어 주세요. ROM과 추출 바이너리는 이슈에 올리지 마세요.

## 권리

원작 게임의 권리는 원 권리자에게 있습니다. 공식 한국어판이 아닙니다. [권리·외부 자료 안내](RIGHTS.md)를 확인하세요.
