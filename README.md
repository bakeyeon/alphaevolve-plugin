# AlphaEvolve Plugin

Google DeepMind의 **AlphaEvolve**와 오픈소스 **OpenEvolve** 구조를 따라 만든 진화형 알고리즘 탐색·코드 최적화 플러그인입니다.
Claude Code와 Antigravity에서 쓸 수 있습니다.

## 설치

**Claude Code**
```
/plugin marketplace add bakeyeon/alphaevolve-plugin
/plugin install alphaevolve@alphaevolve-plugin
```

**Antigravity**: 저장소를 플러그인으로 추가하면 됩니다. 루트의 `plugin.json`을 사용합니다.

## 주요 기능

1. **에이전트 기반 진화 루프 (Mode A)**
   - 별도 패키지나 API 키 없이 에이전트가 직접 변이를 제안합니다.
   - `evolve_local.py`가 후보를 평가하고 `archive.json`과 `best_program.py`를 관리합니다.
   - 명령은 `init`, `sample`, `evaluate`, `status` 네 가지입니다.
2. **OpenEvolve CLI 연동 (Mode B)**
   - `pip install openevolve`와 바로 호환되는 `initial_program.py`, `evaluator.py`, `config.yaml`을 만듭니다.
3. **믿을 수 있는 평가기 템플릿**
   - 정답 기준(정확한 DP)과 비교해 정확성을 판정합니다.
   - 시드를 고정한 무작위 인스턴스 40개와 경계 사례로 테스트합니다.
   - 후보마다 별도 프로세스에서 실행하고 시간 제한을 둡니다.
   - 점수(`combined_score`)는 항상 같은 값이 나오게 품질만 반영합니다. 실행 시간은 중앙값으로 따로 기록합니다.

## 추천 흐름: 3단계 다음에 진화

1. **L1 기본**: 정의를 그대로 옮긴, 확실히 맞는 코드. 평가기의 정답 기준이 됩니다.
2. **L2 깔끔**: 읽기 좋고 실용적인 알고리즘
3. **L3 최적**: 직접 유도할 수 있는 가장 좋은 방법
4. **진화**: L3보다 더 나은 답을 탐색하고 싶을 때만 씁니다. 점수를 코드로 계산할 수 있는 문제여야 합니다.

## 시작 프롬프트 예시

- *"이 알고리즘을 AlphaEvolve 방식으로 진화 탐색 및 성능 최적화해 줘"*
- *"내 최적화 문제를 위한 AlphaEvolve / OpenEvolve 평가기(evaluator)와 초기 프로그램을 구성해 줘"*
- *"휴리스틱 점수를 극대화하도록 함수를 진화적으로 개선해 줘"*

## 구조
```
skills/alphaevolve/SKILL.md                     스킬 설명과 작업 절차
skills/alphaevolve/scripts/scaffold_evolve.py   작업 폴더 생성 (기존 파일은 덮어쓰지 않음)
skills/alphaevolve/scripts/templates/           initial_program.py, evaluator.py, config.yaml, evolve_local.py
```
