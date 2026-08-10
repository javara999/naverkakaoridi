# 통합 웹툰/웹소설 검색(네이버/카카오/리디/노벨피아)

네이버·카카오·리디·노벨피아의 웹툰/웹소설 메타데이터를 한 번에 검색하여 BookOasis 도서에 적용하는 검색형 메타데이터 플러그인입니다.

![검색 결과 화면](docs/screenshot.webp)

## 버전 및 호환 정보

| 항목 | 값 |
| --- | --- |
| 플러그인 버전 | `1.6.2` |
| 플러그인 ID | `naverkakaoridi` |
| 이전 플러그인 ID | `naverkakaoridi_meta` |
| 클래스 | `NaverkakaoridiMetadataProvider` |
| 모듈 | `plugins.metadata.naverkakaoridi.naverkakaoridi` |
| 유형 | 검색형 메타데이터 제공자 |
| 확인한 BookOasis 버전 | `1.9.0` |
| 확인한 BookOasis 커밋 | `56f7e34` |
| 지원 DBMS | `SQLite`, `MariaDB` |
| 문서 작성일 | `2026-08-10` |

이 버전은 BookOasis의 권장 폴더형 플러그인 구조와 DB Gateway 규격을 사용합니다. SQLite와 MariaDB에서 동일한 게이트웨이 쿼리를 사용하며 BookOasis 코어 파일을 수정하지 않습니다.

## 지원 검색 소스

- 네이버웹툰 (`naver_webtoon`)
- 네이버시리즈 (`naver_series`)
- 카카오웹툰 (`kakao_webtoon`)
- 카카오페이지 (`kakaopage`)
- 리디 (`ridibooks`)
- 노벨피아 (`novelpia`)
- 문피아 (`munpia`)

`SOURCES`를 `all`로 설정하면 모든 소스를 순서대로 검색합니다. 일부 소스만 사용할 때는 위 식별자를 쉼표로 구분해 입력합니다.
네이버·카카오·리디·노벨피아·문피아 체크박스를 끄면 `SOURCES` 값과 관계없이 해당 그룹은 검색하지 않습니다.

## 검색 결과와 메타데이터 적용

- 검색 결과 화면의 제목에만 `[출처]`를 붙입니다. 예: `[네이버웹툰] 작품명`
- 원래 제목은 결과의 `raw_title`에 별도로 보관하며, 메타데이터 적용 전에 복원합니다.
- `[출처]` 표시는 BookOasis DB의 제목에 저장되지 않습니다. 이 플러그인은 기존 도서 제목 자체를 변경하지 않습니다.
- 텍스트 메타데이터는 선택한 도서 한 권(`book_id`)에 적용하며, 시리즈 전체 텍스트 적용은 BookOasis의 시리즈 전파 기능이 별도로 처리합니다.
- `같은 시리즈 전체에 표지 적용`이 켜져 있으면 선택한 표지를 같은 보관함·시리즈의 삭제되지 않은 모든 권/화에 적용합니다. BookOasis의 기본 시리즈 전파가 표지를 제외하기 때문에 플러그인이 표지만 별도로 처리합니다.
- 적용 필드는 저자, 출판사, 소개, 링크, 장르, 태그, 평점, 표지입니다.
- 시리즈 전파 시 BookOasis 코어의 현재 동작에 따라 저자, 출판사, 소개, 링크, 평점만 다른 권에 복사되며 장르, 태그, 표지는 전파되지 않습니다.
- 이미지는 한 번만 내려받지만 각 권/화의 전체 `file_path`를 MD5 해시한 고유 표지 파일로 복제합니다. 따라서 특정 권을 영구 삭제해도 다른 권의 표지는 유지됩니다.

## 설정

설정 화면에는 다음 항목만 표시합니다.

| 키 | 유형 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `SEARCH_NAVER` | checkbox | `true` | 네이버웹툰·네이버시리즈 검색 |
| `SEARCH_KAKAO` | checkbox | `true` | 카카오웹툰·카카오페이지 검색 |
| `SEARCH_RIDI` | checkbox | `true` | 리디 검색 |
| `SEARCH_NOVELPIA` | checkbox | `true` | 노벨피아 검색 |
| `SEARCH_MUNPIA` | checkbox | `true` | 문피아 검색 |
| `PROXY_URL` | password | 빈 값 | 검색과 표지 다운로드에 사용할 HTTP(S) 프록시 URL |
| `SEARCH_EXACT` | checkbox | `false` | 정규화한 제목이 검색어와 같은 결과만 표시 |
| `INCLUDE_ADULT` | checkbox | `false` | 성인 플래그가 있는 결과 포함 |
| `APPLY_COVER_TO_SERIES` | checkbox | `true` | 같은 보관함·시리즈의 모든 권/화에 선택한 표지 적용 |
| `APPLY_RATING_TO_SERIES` | checkbox | `true` | 같은 보관함·시리즈의 모든 권/화에 평점과 평점 출처 적용 |
| `NAVER_COOKIE` | password | 빈 값 | 네이버 로그인/연령 제한용 Cookie |
| `KAKAO_COOKIE` | password | 빈 값 | 카카오 로그인/연령 제한용 Cookie |
| `RIDI_COOKIE` | password | 빈 값 | 리디 로그인/연령 제한용 Cookie |
| `MUNPIA_COOKIE` | password | 빈 값 | 문피아 로그인/연령 제한용 Cookie |

다음 항목은 설정 화면에서 숨기고 내부 기본값을 사용합니다.

| 키 | 기본값 |
| --- | --- |
| `SOURCES` | `all` |
| `MAX_RESULTS` | `20` |
| `TIMEOUT` | `10`초 |
| `USER_AGENT` | 내장 브라우저 UA |
| `NOVELPIA_TIMEOUT` | `3`초 |
| `KAKAOPAGE_CATEGORY` | `all` |

Cookie와 프록시 URL 입력란은 화면에서 비밀번호 형식으로 가려지지만 BookOasis 설정 DB에는 설정 JSON의 일부로 저장됩니다. 필요한 값만 입력하고 계정 보안 정책에 맞게 주기적으로 갱신하세요.

프록시는 `http://host:port` 또는 `http://user:password@host:port` 형식을 지원합니다. SOCKS 프록시는 지원하지 않습니다.
리디의 Cloudflare 403은 프록시에서도 발생할 수 있습니다. 공개·데이터센터 프록시보다 신뢰 가능한 고정 프록시를 사용하고, 필요한 경우 `RIDI_COOKIE`도 함께 설정하세요.
프록시는 모든 검색 사이트와 표지 다운로드에 공통 적용됩니다. 노벨피아가 시간 초과되면 5분 동안 노벨피아만 건너뛰고 다른 사이트 검색은 계속합니다.

## 검색 결과 규격

각 결과는 BookOasis 표준 필드인 `title`, `author`, `publisher`, `pubDate`, `cover`, `description`, `link`를 반환합니다. 이 플러그인은 추가로 다음 필드를 반환합니다.

| 필드 | 설명 |
| --- | --- |
| `source` | 사용자에게 표시할 출처 이름 |
| `raw_title` | `[출처]`가 붙지 않은 원래 제목 |
| `isbn` | 원본 검색 결과가 제공하는 ISBN |
| `genre` | 장르 |
| `tags` | 태그 |
| `score` | 원본 평점을 BookOasis 100점 단위로 변환한 값 |

결과 카드의 제목·저자·출판사·출간일은 BookOasis에서 HTML 이스케이프되며, 플러그인도 외부 응답을 텍스트로 정리한 뒤 반환합니다.

## 설치 및 이전 버전에서 업그레이드

최종 폴더 구조는 다음과 같습니다.

```text
plugins/metadata/naverkakaoridi/
├── __init__.py
├── naverkakaoridi.py
├── settings.html
├── settings.css
├── README.md
└── VERSION
```

1. 기존 단일 파일 `plugins/metadata/naverkakaoridi_meta.py`가 있으면 제거하고 위 폴더를 배치합니다.
2. BookOasis 서버를 재시작합니다.
3. 환경설정의 플러그인 목록에서 `통합 웹툰/웹소설 검색(네이버/카카오/리디)`를 확인합니다.
4. 설정을 확인한 뒤 한 번 저장하면 새 키 `PLUGIN_CONFIG_naverkakaoridi`가 사용됩니다.

플러그인 ID가 `naverkakaoridi_meta`에서 `naverkakaoridi`로 변경되었습니다. 버전 `1.0.0`은 새 설정이 아직 비어 있을 때 기존 `PLUGIN_CONFIG_naverkakaoridi_meta` 값을 읽는 호환 폴백을 제공합니다. 활성화 상태 키는 ID에 종속되므로 기존 `PLUGIN_ENABLED_naverkakaoridi_meta` 값은 자동 이전되지 않습니다. 업그레이드 후 새 플러그인의 활성화 상태를 환경설정에서 확인하세요.

## 샘플 업데이트

BookOasis의 플러그인 설정 화면에서 샘플 업데이트 버튼을 표시하도록 `update_manifest`를 제공합니다.

- 원격 원본: `https://github.com/javara999/naverkakaoridi`
- 업데이트 방식: GitHub raw 파일 다운로드
- 교체 대상: `naverkakaoridi.py`, `settings.html`, `settings.css`, `__init__.py`, `README.md`, `VERSION`
- 업데이트 조건: 로컬 `VERSION`의 `plugin version` 값이 GitHub의 값보다 낮을 때만 실행

버전이 같거나 로컬 버전이 더 높으면 BookOasis 정책에 따라 업데이트가 차단됩니다.
`1.5.0` 이하에서 처음 업그레이드할 때는 구버전 매니페스트에 `settings.html`과 `settings.css`가 없으므로 저장소 폴더 전체를 교체한 뒤 BookOasis를 재시작해야 합니다.

## 제한 사항

- 각 서비스의 비공개/비공식 웹 엔드포인트와 HTML 응답을 사용하므로 서비스 개편이나 접근 정책 변경 시 검색이 중단될 수 있습니다.
- BookOasis는 플러그인에 단권 모드와 시리즈 모드를 구분하여 전달하지 않습니다. 따라서 `APPLY_COVER_TO_SERIES`가 켜져 있으면 단권 메뉴에서 적용하더라도 같은 시리즈 전체의 표지가 변경됩니다.
- 표지 URL이 없는 결과는 검색 목록에서 제외됩니다.
- 로그인 또는 연령 확인이 필요한 결과는 유효한 Cookie와 해당 서비스의 정책에 따른 접근 권한이 필요할 수 있습니다.
- 외부 서비스별 요청 오류는 해당 소스 결과만 제외하고 다른 소스 검색은 계속 진행합니다.

## 변경 이력

### 1.6.2 - 2026-08-11

- 검색 소스 5개를 `검색 소스` 한 줄의 가로 체크박스로 정리
- 설정 화면에서 세부 소스, 결과 수, 제한 시간, User-Agent, 노벨피아 제한 시간, 카카오페이지 카테고리를 숨기고 기본값 적용
- 검색 소스·메타 적용 체크박스, 프록시, 쿠키 설정만 표시

### 1.6.1 - 2026-08-11

- 네이버, 카카오, 리디, 노벨피아, 문피아 검색 여부를 개별 체크박스로 설정
- 기존 `SOURCES` 세부 사이트 설정과 이전 저장값 호환 유지

### 1.6.0 - 2026-08-11

- 문피아(`munpia`) 공식 검색 API 기반 검색 소스 추가
- 문피아 제목, 작가, 소개, 장르, 태그, 표지, 최근 갱신일 수집
- 선택적 `MUNPIA_COOKIE` 설정과 공통 프록시 적용

### 1.5.2 - 2026-08-10

- `1.5.1` 전환 업데이트에서 누락된 커스텀 설정 UI 파일을 다시 받을 수 있도록 복구 버전 배포

### 1.5.1 - 2026-08-10

- 플러그인 설정을 클릭해서 펼치는 커스텀 설정 화면 추가
- 기존 설정 키, 기본값 및 저장 방식 유지

### 1.5.0 - 2026-08-10

- BookOasis v1.9.0 MariaDB 게이트웨이 및 스키마 호환
- MariaDB strict mode에 맞춰 선택 필드를 `NULL`, 평점을 정수로 전달
- 동일 메타데이터 재적용 시 MariaDB 변경 행 수가 0이어도 대상 도서가 존재하면 성공 처리
- SQLite/MariaDB 공통 SQL 비교 연산자와 시리즈 적용 건수 처리 사용

### 1.4.3 - 2026-07-21

- BookOasis 샘플 업데이트 버튼 지원을 위한 `update_manifest` 추가
- GitHub raw 기반 업데이트용 `VERSION` 파일 추가
- 업데이트 대상 파일을 `naverkakaoridi.py`, `__init__.py`, `README.md`, `VERSION`으로 선언

### 1.4.2 - 2026-07-21

- BookOasis v1.2.8 `PluginDatabaseGateway`의 `execute`/`execute_many` API 적용
- 제거된 `transaction()` 호출로 메타데이터 적용이 실패하던 문제 수정

### 1.4.1 - 2026-07-21

- 노벨피아 전용 요청 제한 시간 추가(기본 3초)
- 노벨피아 네트워크 장애 후 5분 쿨다운으로 반복 검색 지연 방지
- 기존 공통 프록시는 모든 검색 사이트와 표지 다운로드에 계속 적용

### 1.4.0 - 2026-07-21

- 플러그인 설정에 `PROXY_URL` 추가
- 검색·상세정보·표지 다운로드 요청에 동일한 HTTP(S) 프록시 적용
- 프록시별 응답 캐시 분리 및 URL 형식 검증

### 1.3.1 - 2026-07-21

- 라이브러리 우클릭 메타 검색에서도 대표 권과 관계없이 보이도록 같은 시리즈 전체에 평점 적용
- 다른 권의 기존 작품 설명은 보존하고 평점 출처 라벨만 교체·추가
- `APPLY_RATING_TO_SERIES` 설정 추가

### 1.3.0 - 2026-07-21

- 네이버웹툰·네이버시리즈·카카오페이지·리디 평점을 BookOasis 100점 단위로 변환하여 적용
- 카카오웹툰은 공개 응답에 평점이 포함된 경우 적용
- 작품 설명 앞에 원본 평점과 평점 출처 표시
- 공개 검색 응답에 평점이 없는 노벨피아는 평점 적용 제외

### 1.2.0 - 2026-07-20

- BookOasis 1.2.1 `books` 스키마의 `isbn`, `release_date`, `metadata_locked` 반영
- 빈 ISBN·출간일은 기존 DB 값을 유지하도록 처리
- WebP 변환 실패 시 원본 바이트를 `.webp` 파일로 저장하지 않도록 수정
- 네이버·카카오 상세 조회를 최대 4개 병렬 처리하고, 중복·무관 결과를 상세 조회 전에 제외

### 1.1.0 - 2026-07-15

- 노벨피아(`novelpia`) 검색 소스 추가
- 노벨피아 비공식 검색 API(`POST /proc/novelsearch/{검색어}`)를 사용해 제목·표지·작가·최근 갱신일을 조회
- 노벨피아 결과의 연령 등급(`novel_age`)이 15 이상이면 `INCLUDE_ADULT`가 꺼진 경우 목록에서 제외
- 표지가 없는 노벨피아 원작 항목은 기존 규칙대로 검색 결과에서 자동 제외

### 1.0.2 - 2026-07-15

- 검색 결과 관련도 필터 추가: 정규화한 검색어가 결과 제목과 부분 일치하지 않으면 목록에서 제외
- 네이버웹툰 등 원본 검색 API가 유사도 기반으로 무관한 작품을 함께 반환하는 문제를 완화
- `SEARCH_EXACT`(완전 일치) 옵션이 꺼져 있을 때만 적용되며, 부제·권 표시가 붙은 정상 결과는 그대로 유지

### 1.0.1 - 2026-07-15

- BookOasis의 시리즈 메타 전파에서 제외되는 표지를 플러그인이 같은 시리즈 전체에 별도로 적용
- 단권 표지만 유지할 수 있도록 `APPLY_COVER_TO_SERIES` 설정 추가
- 다른 보관함 및 삭제된 도서에는 표지가 전파되지 않도록 범위 제한
- 권/화마다 전체 `file_path` 기반 고유 표지 파일을 생성하여 개별 도서 영구 삭제 시에도 나머지 표지가 유지되도록 처리
- 대상 메타데이터와 시리즈 표지 DB 갱신을 하나의 트랜잭션으로 처리

### 1.0.0 - 2026-07-15

- 최신 권장 폴더형 플러그인 구조로 전환
- 클래스/파일/폴더/ID를 `NaverkakaoridiMetadataProvider`/`naverkakaoridi` 규칙에 맞춤
- 플러그인의 직접 DB 접근을 제거하고 `PluginDatabaseGateway` 사용
- 메타데이터 적용 범위를 선택한 도서 한 권으로 제한
- 검색 결과에만 `[출처]`를 표시하고 적용 시 원래 제목을 복원
- 숫자·체크박스·비밀번호 설정 필드를 최신 `config_schema` 유형에 맞춤
- 기존 `naverkakaoridi_meta` 설정을 위한 읽기 호환 폴백 추가
- BookOasis 표준 전체 경로 기반 표지 해시 및 조건부 캐시 갱신 적용
