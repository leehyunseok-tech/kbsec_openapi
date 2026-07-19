"""데이터/코드 생성 파이프라인 스크립트 모음 (런타임 코드가 아님).

- generate_mst: 종목마스터 파이프라인 — mst/origin/*.mst 원본을 갱신해 놓고
  `uv run python -m manage.generate.generate_mst`를 실행하면 관련 문서(xlsx/md)와
  런타임 데이터(mst/api/openapi_field_*.mst)가 전부 재생성된다.
- convert_xlsx_to_md / generate_api_list / generate_api_client / generate_api_docs:
  KB API 명세(xlsx) → md → api-list.md/json → src/api/*.py 생성 코드로 이어지는
  API 명세 파이프라인. 상세 설명·실행 시점은 docs/개발환경/manage.md 참고.
"""
