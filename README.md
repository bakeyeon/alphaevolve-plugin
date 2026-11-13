# AlphaEvolve Plugin for Antigravity

Google DeepMind의 **AlphaEvolve** 및 오픈소스 **OpenEvolve** 아키텍처를 기반으로 한 진화형 알고리즘 탐색 및 코드 최적화 플러그인입니다.

## 주요 기능

1. **에이전트 기반 네이티브 진화 루프 (Native Agent-Driven AlphaEvolve Loop)**
   - 별도의 외부 패키지나 추가 API 키 설정 없이 Antigravity가 직접 초기 프로그램(`initial_program.py`), 자동 평가기(`evaluator.py`), 세대별 아카이브(`archive.json`)를 관리하며 `# EVOLVE-BLOCK` 영역을 반복적으로 변이·교차·검증합니다.
2. **OpenEvolve CLI 워크스페이스 스캐폴딩 및 연동**
   - `openevolve` 패키지(`pip install openevolve`)와 즉시 호환되는 `initial_program.py`, `evaluator.py`, `config.yaml` 템플릿을 생성하고 실행합니다.
3. **정량적 벤치마크 및 품질-다양성(MAP-Elites) 추적**
   - 매 세대 코드의 정확성 검증, 실행 시간 측정, `combined_score` 향상 추이를 기록하고 최적 프로그램(`best_program.py`)을 자동으로 보존합니다.

## 시작 프롬프트 예시

- *"이 알고리즘을 AlphaEvolve 방식으로 진화 탐색 및 성능 최적화해 줘"*
- *"내 최적화 문제를 위한 AlphaEvolve / OpenEvolve 평가기(evaluator)와 초기 프로그램을 구성해 줘"*
- *"휴리스틱 점수를 극대화하도록 함수를 진화적으로 개선해 줘"*
