"""프로젝트 관리용 스크립트 모음 (런타임 코드가 아닌 생성/갱신 파이프라인).

- generate_mst: 종목마스터 파이프라인 — mst/origin/*.mst 원본을 갱신해 놓고
  `uv run python -m src.manage.generate_mst`를 실행하면 관련 문서(xlsx/md)와
  런타임 데이터(mst/api/openapi_field_*.mst)가 전부 재생성된다.
"""
