# -*- coding: utf-8 -*-
import hashlib
import html
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image
from plugins.metadata.base import BaseMetadataProvider


class NaverKakaoRidiMetadataProvider(BaseMetadataProvider):
    id = "naverkakaoridi"
    legacy_id = "naverkakaoridi_meta"
    name = "네이버/카카오/리디 메타 검색"
    is_searchable = True
    config_schema = [
        {
            "key": "SOURCES",
            "label": "검색 사이트",
            "type": "text",
            "required": False,
            "default": "all",
            "description": "기본값 all. 사용 가능: all, naver_webtoon, naver_series, kakao_webtoon, kakaopage, ridibooks. 여러 개는 콤마로 구분.",
        },
        {
            "key": "MAX_RESULTS",
            "label": "최대 검색 결과",
            "type": "number",
            "required": False,
            "default": "20",
            "description": "기본값 20. 전체 사이트 결과를 합쳐 반환할 최대 개수.",
        },
        {
            "key": "TIMEOUT",
            "label": "요청 제한 시간",
            "type": "number",
            "required": False,
            "default": "10",
            "description": "기본값 10초. 외부 사이트 응답 대기 시간.",
        },
        {
            "key": "USER_AGENT",
            "label": "User-Agent",
            "type": "text",
            "required": False,
            "default": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
            "description": "기본 브라우저 User-Agent. 차단 회피가 필요할 때만 변경.",
        },
        {
            "key": "SEARCH_EXACT",
            "label": "정확한 제목만",
            "type": "checkbox",
            "required": False,
            "default": False,
            "description": "true면 검색어와 제목이 거의 같은 결과만 사용.",
        },
        {
            "key": "INCLUDE_ADULT",
            "label": "성인 결과 포함",
            "type": "checkbox",
            "required": False,
            "default": False,
            "description": "true면 19세/성인 플래그가 있는 결과도 포함.",
        },
        {
            "key": "NAVER_COOKIE",
            "label": "네이버 Cookie",
            "type": "password",
            "required": False,
            "default": "",
            "description": "기본값 공백. 연령 제한/로그인 필요 작품 검색이 필요할 때만 입력.",
        },
        {
            "key": "KAKAO_COOKIE",
            "label": "카카오 Cookie",
            "type": "password",
            "required": False,
            "default": "",
            "description": "기본값 공백. 연령 제한/로그인 필요 작품 검색이 필요할 때만 입력.",
        },
        {
            "key": "RIDI_COOKIE",
            "label": "리디 Cookie",
            "type": "password",
            "required": False,
            "default": "",
            "description": "기본값 공백. 연령 제한/로그인 필요 작품 검색이 필요할 때만 입력.",
        },
        {
            "key": "KAKAOPAGE_CATEGORY",
            "label": "카카오페이지 카테고리",
            "type": "text",
            "required": False,
            "default": "all",
            "description": "기본값 all. comic=10, novel=11, book=16 또는 숫자 category_uid 입력 가능.",
        },
    ]

    SOURCE_ORDER = ("naver_webtoon", "naver_series", "kakao_webtoon", "kakaopage", "ridibooks")
    SOURCE_META = {
        "naver_webtoon": {
            "label": "네이버웹툰",
            "group": "naver",
            "badge": "N",
            "icon": "fa-solid fa-n",
            "color": "#03c75a",
        },
        "naver_series": {
            "label": "네이버시리즈",
            "group": "naver",
            "badge": "N",
            "icon": "fa-solid fa-n",
            "color": "#03c75a",
        },
        "kakao_webtoon": {
            "label": "카카오웹툰",
            "group": "kakao",
            "badge": "K",
            "icon": "fa-solid fa-k",
            "color": "#fee500",
        },
        "kakaopage": {
            "label": "카카오페이지",
            "group": "kakao",
            "badge": "K",
            "icon": "fa-solid fa-k",
            "color": "#fee500",
        },
        "ridibooks": {
            "label": "리디",
            "group": "ridi",
            "badge": "R",
            "icon": "fa-solid fa-r",
            "color": "#1f8ce6",
        },
    }
    _cache = {}

    def search(self, db_type, query):
        query = (query or "").strip()
        if not query:
            return []

        cfg = self._get_config(db_type)
        max_results = self._int(cfg.get("MAX_RESULTS"), 20, 1, 100)
        sources = self._sources(cfg.get("SOURCES"))

        results = []
        for source in self.SOURCE_ORDER:
            if source not in sources:
                continue
            try:
                if source == "naver_webtoon":
                    results.extend(self._search_naver_webtoon(query, cfg))
                elif source == "naver_series":
                    results.extend(self._search_naver_series(query, cfg))
                elif source == "kakao_webtoon":
                    results.extend(self._search_kakao_webtoon(query, cfg))
                elif source == "kakaopage":
                    results.extend(self._search_kakaopage(query, cfg))
                elif source == "ridibooks":
                    results.extend(self._search_ridibooks(query, cfg))
            except Exception as e:
                print(f"[NaverKakaoRidiMetadataProvider] {source} search failed: {e}")
            if len(results) >= max_results:
                break

        results = [r for r in results if (r.get("cover") or "").strip()]
        results = self._dedupe(results)
        if self._truthy(cfg.get("SEARCH_EXACT")):
            nq = self._normalize(query)
            results = [r for r in results if self._normalize(r.get("title")) == nq]
        return results[:max_results]

    def apply(self, db_type, book_id, item_data):
        gateway = self.get_db_gateway(db_type)
        try:
            book = gateway.fetch_one("SELECT file_path, series_name, library_id FROM books WHERE id = ?", (book_id,))
            if not book:
                return False, "대상 도서를 찾을 수 없습니다."

            cover_filename = self._save_cover(book, item_data.get("cover"))
            description = self._clean_text(item_data.get("description"))
            author = self._clean_text(item_data.get("author"))
            publisher = self._clean_text(item_data.get("publisher"))
            link = item_data.get("link") or ""
            genre = self._clean_text(item_data.get("genre"))
            tags = self._clean_text(item_data.get("tags"))
            score = self._clean_text(item_data.get("score"))

            series_name = self._row_get(book, "series_name")
            library_id = self._row_get(book, "library_id")
            if series_name:
                where_sql = "series_name = ? AND library_id = ?"
                where_args = (series_name, library_id)
            else:
                where_sql = "id = ?"
                where_args = (book_id,)

            count_row = gateway.fetch_one(f"SELECT COUNT(*) AS cnt FROM books WHERE {where_sql}", where_args)
            count = int((self._row_get(count_row, "cnt", 0) if count_row else 0) or 0)

            gateway.execute(
                f"""
                UPDATE books
                SET author = ?,
                    publisher = ?,
                    summary = ?,
                    link = ?,
                    genre = COALESCE(NULLIF(?, ''), genre),
                    tags = COALESCE(NULLIF(?, ''), tags),
                    score = COALESCE(NULLIF(?, ''), score),
                    cover_image = COALESCE(NULLIF(?, ''), cover_image),
                    cover_updated_at = CURRENT_TIMESTAMP
                WHERE {where_sql}
                """,
                (author, publisher, description, link, genre, tags, score, cover_filename or "", *where_args),
            )
            title = item_data.get("title") or series_name or book_id
            return True, f'"{title}" 메타데이터를 {count}개 항목에 반영했습니다.'
        except Exception as e:
            return False, f"DB 업데이트 오류: {e}"

    def _search_naver_webtoon(self, query, cfg):
        url = "https://comic.naver.com/api/search/all?" + urllib.parse.urlencode({"keyword": query})
        data = self._get_json(url, cfg, headers=self._naver_headers(cfg, "https://comic.naver.com/"))
        groups = (
            "searchWebtoonResult",
            "searchBestChallengeResult",
            "searchChallengeResult",
            "searchNbooksComicResult",
        )
        results = []
        for group in groups:
            for item in self._as_list(data.get(group)):
                title_id = item.get("titleId") or item.get("contentId") or item.get("id")
                title = self._clean_text(item.get("titleName") or item.get("title") or item.get("name"))
                if not title or not title_id:
                    continue
                if self._is_adult(item) and not self._truthy(cfg.get("INCLUDE_ADULT")):
                    continue

                detail = self._naver_webtoon_detail(title_id, cfg) or {}
                authors = detail.get("communityArtists") or item.get("communityArtists") or []
                genre_list = detail.get("genreList") or item.get("genreList") or []
                tags = detail.get("curationTagList") or item.get("curationTagList") or []
                results.append(
                    self._item(
                        source_key="naver_webtoon",
                        title=detail.get("titleName") or title,
                        author=self._join_names(authors),
                        publisher="네이버웹툰",
                        cover=detail.get("thumbnailUrl") or item.get("thumbnailUrl"),
                        description=detail.get("synopsis") or item.get("synopsis") or "",
                        link=f"https://comic.naver.com/webtoon/list?titleId={title_id}",
                        genre=self._join_names(genre_list),
                        tags=self._join_names(tags),
                        pub_date="",
                        score=str(detail.get("starScore") or ""),
                    )
                )
        return results

    def _naver_webtoon_detail(self, title_id, cfg):
        url = "https://comic.naver.com/api/article/list/info?" + urllib.parse.urlencode({"titleId": title_id})
        try:
            return self._get_json(url, cfg, headers=self._naver_headers(cfg, "https://comic.naver.com/"))
        except Exception:
            return {}

    def _search_naver_series(self, query, cfg):
        params = urllib.parse.urlencode({"t": "all", "fs": "comic", "q": query})
        search_url = f"https://series.naver.com/search/search.series?{params}"
        text = self._get_text(search_url, cfg, headers=self._naver_headers(cfg, "https://series.naver.com/"))
        product_nos = []
        for m in re.finditer(r"/comic/detail\.series\?productNo=(\d+)", text):
            if m.group(1) not in product_nos:
                product_nos.append(m.group(1))

        results = []
        for product_no in product_nos[: self._int(cfg.get("MAX_RESULTS"), 20, 1, 100)]:
            item = self._naver_series_detail(product_no, cfg)
            if item:
                results.append(item)
        return results

    def _naver_series_detail(self, product_no, cfg):
        url = f"https://series.naver.com/comic/detail.series?productNo={product_no}"
        text = self._get_text(url, cfg, headers=self._naver_headers(cfg, "https://series.naver.com/"))
        meta = self._meta_tags(text)
        title = self._clean_text(meta.get("og:title") or "")
        desc = self._clean_text(meta.get("og:description") or "")
        if not title:
            return None

        author = ""
        m = re.search(r"(?:글|그림|작가)\s*[:：]\s*([^,\n]+)", desc)
        if m:
            author = self._clean_text(m.group(1))
        tags = ", ".join(re.findall(r"#([^\s#]+)", desc))
        return self._item(
            source_key="naver_series",
            title=title,
            author=author,
            publisher="네이버시리즈",
            cover=meta.get("og:image") or "",
            description=desc,
            link=url,
            genre="",
            tags=tags,
            pub_date="",
            score="",
        )

    def _search_kakao_webtoon(self, query, cfg):
        params = urllib.parse.urlencode({"word": query, "offset": 0, "limit": self._int(cfg.get("MAX_RESULTS"), 20, 1, 100)})
        url = f"https://gateway-kw.kakao.com/search/v2/content?{params}"
        data = self._get_json(url, cfg, headers=self._kakao_webtoon_headers(cfg, query))
        contents = ((data.get("data") or {}).get("content")) or []

        results = []
        for item in contents:
            if item.get("adult") and not self._truthy(cfg.get("INCLUDE_ADULT")):
                continue
            content_id = item.get("id") or item.get("contentId")
            detail = self._kakao_webtoon_detail(content_id, cfg) if content_id else {}
            merged = dict(item)
            merged.update(detail)
            title = self._clean_text(merged.get("title"))
            if not title or not content_id:
                continue
            seo_id = urllib.parse.quote(str(merged.get("seoId") or title.replace(" ", "-")), safe="")
            results.append(
                self._item(
                    source_key="kakao_webtoon",
                    title=title,
                    author=self._kakao_author_text(merged.get("authors")),
                    publisher=self._kakao_publisher(merged.get("authors")) or "카카오웹툰",
                    cover=merged.get("thumbnailImage") or merged.get("sharingThumbnailImage") or merged.get("titleImageA") or merged.get("backgroundImage"),
                    description=merged.get("synopsis") or merged.get("catchphraseThreeLines") or merged.get("catchphraseTwoLines") or "",
                    link=f"https://webtoon.kakao.com/content/{seo_id}/{content_id}",
                    genre=merged.get("genre") or "",
                    tags="",
                    pub_date="",
                    score=str(merged.get("rating") or ""),
                )
            )
        return results

    def _kakao_webtoon_detail(self, content_id, cfg):
        url = f"https://gateway-kw.kakao.com/decorator/v2/decorator/contents/{content_id}"
        try:
            data = self._get_json(url, cfg, headers=self._kakao_webtoon_headers(cfg, ""))
            return data.get("data") or {}
        except Exception:
            return {}

    def _search_kakaopage(self, query, cfg):
        category = self._kakaopage_category(cfg.get("KAKAOPAGE_CATEGORY"))
        params = urllib.parse.urlencode(
            {
                "keyword": query,
                "category_uid": category,
                "is_complete": "false",
                "sort_type": "ACCURACY",
                "page": 0,
                "size": self._int(cfg.get("MAX_RESULTS"), 20, 1, 100),
            }
        )
        url = f"https://bff-page.kakao.com/api/gateway/api/v2/search/series?{params}"
        data = self._get_json(url, cfg, headers=self._kakaopage_headers(cfg, query))
        items = ((data.get("result") or {}).get("list")) or []

        results = []
        for item in items:
            if self._is_kakaopage_adult(item) and not self._truthy(cfg.get("INCLUDE_ADULT")):
                continue
            series_id = item.get("series_id") or item.get("id")
            detail = self._kakaopage_detail(series_id, cfg) if series_id else {}
            merged = dict(item)
            merged.update(detail)
            title = self._clean_text(merged.get("title"))
            if not title or not series_id:
                continue
            results.append(
                self._item(
                    source_key="kakaopage",
                    title=title,
                    author=self._clean_text(merged.get("authors")),
                    publisher="카카오페이지",
                    cover=self._kakaopage_image(merged.get("thumbnail")),
                    description=merged.get("description") or "",
                    link=f"https://page.kakao.com/content/{series_id}",
                    genre=self._clean_text(merged.get("sub_category") or merged.get("category")),
                    tags=self._clean_text(merged.get("category")),
                    pub_date=merged.get("start_sale_dt") or merged.get("last_slide_added_dt") or "",
                    score=self._kakaopage_score(merged),
                )
            )
        return results

    def _kakaopage_detail(self, series_id, cfg):
        url = "https://bff-page.kakao.com/api/gateway/api/v1/content/overview?" + urllib.parse.urlencode({"series_id": series_id})
        try:
            data = self._get_json(url, cfg, headers=self._kakaopage_headers(cfg, ""))
            return (data.get("result") or {}).get("content") or {}
        except Exception:
            return {}

    def _search_ridibooks(self, query, cfg):
        url = "https://ridibooks.com/search?" + urllib.parse.urlencode({"q": query})
        text = self._get_text(url, cfg, headers=self._ridi_headers(cfg, url))
        data = self._next_data(text)
        cells = (
            (((data.get("props") or {}).get("pageProps") or {}).get("gridData") or {})
            .get("riGrid", {})
            .get("grid", {})
            .get("cells", [])
        )

        books = []
        for cell in cells:
            book_cell = cell.get("cell__SearchBookListWithTab") if isinstance(cell, dict) else None
            if book_cell:
                books.extend(book_cell.get("books") or [])

        results = []
        for item in books[: self._int(cfg.get("MAX_RESULTS"), 20, 1, 100)]:
            book = item.get("book") or {}
            if book.get("isAdultOnly") and not self._truthy(cfg.get("INCLUDE_ADULT")):
                continue
            rid = item.get("id") or book.get("id")
            title = ((book.get("series") or {}).get("title") or (item.get("title") or {}).get("main") or book.get("title"))
            if not rid or not title:
                continue
            authors = book.get("authors") or []
            categories = book.get("categories") or []
            publication = book.get("publicationInfo") or {}
            intro = book.get("introduction") or {}
            thumbnail = (book.get("series") or {}).get("thumbnail") or book.get("thumbnail") or {}
            results.append(
                self._item(
                    source_key="ridibooks",
                    title=title,
                    author=self._join_names(authors),
                    publisher=publication.get("name") or "리디",
                    cover=thumbnail.get("xxlarge") or thumbnail.get("large") or thumbnail.get("small") or "",
                    description=intro.get("description") or "",
                    link=f"https://ridibooks.com/books/{rid}",
                    genre=self._join_names(categories),
                    tags=(book.get("webTitle") or "").strip("[]"),
                    pub_date="",
                    score=self._ridi_score(book),
                )
            )
        return results

    def get_context_menu_items(self, db_type, context):
        return [
            {
                "id": "open_naver_search",
                "label": "네이버에서 제목 검색",
                "icon": self.SOURCE_META["naver_webtoon"]["icon"],
            },
            {
                "id": "open_kakao_search",
                "label": "카카오에서 제목 검색",
                "icon": self.SOURCE_META["kakao_webtoon"]["icon"],
            },
            {
                "id": "open_ridi_search",
                "label": "리디에서 제목 검색",
                "icon": self.SOURCE_META["ridibooks"]["icon"],
            },
        ]

    def run_context_menu_action(self, db_type, action_id, context):
        title = ((context or {}).get("book_title") or "").strip()
        if not title:
            return {"success": False, "error": "도서 제목 정보가 없어 검색을 실행할 수 없습니다."}

        if action_id == "open_naver_search":
            url = "https://search.naver.com/search.naver?" + urllib.parse.urlencode({"query": title})
        elif action_id == "open_kakao_search":
            url = "https://page.kakao.com/search/result?" + urllib.parse.urlencode({"keyword": title})
        elif action_id == "open_ridi_search":
            url = "https://ridibooks.com/search?" + urllib.parse.urlencode({"q": title})
        else:
            return {"success": False, "error": f"지원하지 않는 액션입니다: {action_id}"}

        return {"success": True, "message": "검색 페이지를 새 탭으로 엽니다.", "open_url": url}

    def _get_config(self, db_type):
        defaults = {f["key"]: f.get("default", "") for f in self.config_schema}
        loaded = False
        try:
            config = self.get_plugin_config(db_type, default={})
            if isinstance(config, str):
                config = json.loads(config)
            if isinstance(config, dict) and config:
                defaults.update(config)
                loaded = True
        except Exception as e:
            print(f"[NaverKakaoRidiMetadataProvider] config load failed: {e}")

        if not loaded:
            try:
                value = self.get_db_gateway(db_type).get_setting(f"PLUGIN_CONFIG_{self.legacy_id}", None)
                if value:
                    defaults.update(json.loads(value))
            except Exception:
                pass
        return defaults

    def _get_json(self, url, cfg, headers=None):
        body, response = self._request(url, cfg, headers=headers or {})
        charset = response.headers.get_content_charset() or "utf-8"
        try:
            text = body.decode("utf-8")
        except Exception:
            text = body.decode(charset, errors="replace")
        return json.loads(text)

    def _get_text(self, url, cfg, headers=None):
        body, response = self._request(url, cfg, headers=headers or {})
        charset = response.headers.get_content_charset()
        if charset:
            return body.decode(charset, errors="replace")
        for enc in ("utf-8", "cp949", "euc-kr"):
            try:
                return body.decode(enc)
            except Exception:
                pass
        return body.decode("utf-8", errors="replace")

    def _request(self, url, cfg, headers=None):
        ttl = 60
        key = (url, tuple(sorted((headers or {}).items())))
        cached = self._cache.get(key)
        if cached and time.time() - cached[0] < ttl:
            return cached[1], cached[2]

        merged_headers = {"User-Agent": cfg.get("USER_AGENT") or self.config_schema[3]["default"]}
        merged_headers.update(headers or {})
        req = urllib.request.Request(url, headers=merged_headers)
        try:
            response = urllib.request.urlopen(req, timeout=self._int(cfg.get("TIMEOUT"), 10, 1, 60))
            body = response.read()
            self._cache[key] = (time.time(), body, response)
            return body, response
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"HTTP {e.code}: {detail}") from e

    def _save_cover(self, book, cover_url):
        if not cover_url:
            return None
        try:
            library_id = self._row_get(book, "library_id")
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            covers_dir = os.path.join(base_dir, "covers", str(library_id))
            os.makedirs(covers_dir, exist_ok=True)

            name_source = self._row_get(book, "series_name") or os.path.basename(self._row_get(book, "file_path", ""))
            book_hash = hashlib.md5(name_source.encode("utf-8")).hexdigest()
            filename = f"book_{book_hash}.webp"
            dest_path = os.path.join(covers_dir, filename)

            req = urllib.request.Request(cover_url, headers={"User-Agent": self.config_schema[3]["default"]})
            with urllib.request.urlopen(req, timeout=10) as response:
                img_data = response.read()
            try:
                with Image.open(io.BytesIO(img_data)) as img:
                    img.save(dest_path, "WEBP", quality=82)
            except Exception:
                with open(dest_path, "wb") as f:
                    f.write(img_data)
            return f"{library_id}/{filename}"
        except Exception as e:
            print(f"[NaverKakaoRidiMetadataProvider] cover download failed: {e}")
            return None

    def _item(self, source_key, title, author, publisher, cover, description, link, genre, tags, pub_date, score):
        source_meta = self.SOURCE_META.get(source_key, {})
        return {
            "title": self._clean_text(title),
            "author": self._clean_text(author),
            "publisher": self._clean_text(publisher),
            "pubDate": self._clean_text(pub_date),
            "cover": cover or "",
            "description": self._clean_text(description),
            "link": link or "",
            "genre": self._clean_text(genre),
            "tags": self._clean_text(tags),
            "score": self._clean_text(score),
            "source": source_meta.get("label", source_key),
            "sourceKey": source_meta.get("group", source_key),
            "sourceLabel": source_meta.get("label", source_key),
            "sourceIcon": source_meta.get("badge", ""),
            "sourceIconClass": source_meta.get("icon", ""),
            "sourceColor": source_meta.get("color", ""),
        }

    def _row_get(self, row, key, default=None):
        try:
            return row[key]
        except Exception:
            return getattr(row, key, default)

    def _naver_headers(self, cfg, referer):
        headers = {"Accept": "application/json, text/html;q=0.9,*/*;q=0.8", "Referer": referer}
        if cfg.get("NAVER_COOKIE"):
            headers["Cookie"] = cfg.get("NAVER_COOKIE")
        return headers

    def _kakaopage_headers(self, cfg, query):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://page.kakao.com",
            "Referer": "https://page.kakao.com/search/result?" + urllib.parse.urlencode({"keyword": query}),
            "User-Agent": (cfg.get("USER_AGENT") or self.config_schema[3]["default"]) + " KakaoPageWeb/ssr",
        }
        if cfg.get("KAKAO_COOKIE"):
            headers["Cookie"] = cfg.get("KAKAO_COOKIE")
        return headers

    def _kakao_webtoon_headers(self, cfg, query):
        headers = {
            "Accept": "application/json",
            "Referer": "https://webtoon.kakao.com/search?" + urllib.parse.urlencode({"keyword": query}),
        }
        if cfg.get("KAKAO_COOKIE"):
            headers["Cookie"] = cfg.get("KAKAO_COOKIE")
        return headers

    def _ridi_headers(self, cfg, referer):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": referer,
        }
        if cfg.get("RIDI_COOKIE"):
            headers["Cookie"] = cfg.get("RIDI_COOKIE")
        return headers

    def _meta_tags(self, text):
        result = {}
        pattern = re.compile(r'<meta\s+([^>]+)>', re.I)
        attr_pattern = re.compile(r'([a-zA-Z_:.-]+)\s*=\s*["\']([^"\']*)["\']')
        for tag in pattern.findall(text):
            attrs = {k.lower(): html.unescape(v) for k, v in attr_pattern.findall(tag)}
            key = attrs.get("property") or attrs.get("name")
            if key and "content" in attrs:
                result[key] = attrs["content"]
        return result

    def _next_data(self, text):
        marker = "__NEXT_DATA__"
        marker_pos = text.find(marker)
        if marker_pos < 0:
            return {}
        start = text.find(">", marker_pos)
        end = text.find("</script>", start)
        if start < 0 or end < 0:
            return {}
        try:
            return json.loads(text[start + 1 : end])
        except Exception:
            return {}

    def _clean_text(self, value):
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value if v)
        value = html.unescape(str(value))
        value = re.sub(r"<[^>]+>", " ", value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _join_names(self, values):
        if not values:
            return ""
        names = []
        for value in values if isinstance(values, list) else [values]:
            if isinstance(value, dict):
                name = (
                    value.get("name")
                    or value.get("description")
                    or value.get("tagName")
                    or value.get("title")
                    or value.get("displayName")
                )
            else:
                name = value
            name = self._clean_text(name)
            if name and name not in names:
                names.append(name)
        return ", ".join(names)

    def _kakao_author_text(self, authors):
        if isinstance(authors, str):
            return self._clean_text(authors)
        if not isinstance(authors, list):
            return ""
        names = []
        for author in sorted(authors, key=lambda x: x.get("order", 0) if isinstance(x, dict) else 0):
            if not isinstance(author, dict):
                continue
            if author.get("type") == "PUBLISHER":
                continue
            name = self._clean_text(author.get("name"))
            role = self._clean_text(author.get("type"))
            if name:
                names.append(f"{name} ({role})" if role else name)
        return ", ".join(names)

    def _kakao_publisher(self, authors):
        if not isinstance(authors, list):
            return ""
        for author in authors:
            if isinstance(author, dict) and author.get("type") == "PUBLISHER":
                return self._clean_text(author.get("name"))
        return ""

    def _kakaopage_image(self, value):
        if not value:
            return ""
        if str(value).startswith("http"):
            return value
        return "https://page-images.kakaoentcdn.com/download/resource?" + urllib.parse.urlencode({"kid": value})

    def _kakaopage_category(self, value):
        value = (value or "all").strip().lower()
        return {"all": 0, "comic": 10, "webtoon": 10, "novel": 11, "book": 16}.get(value, self._int(value, 0, 0, 9999))

    def _kakaopage_score(self, item):
        prop = item.get("service_property") if isinstance(item, dict) else None
        if not isinstance(prop, dict):
            return ""
        count = prop.get("rating_count") or 0
        total = prop.get("rating_sum") or 0
        if count:
            return f"{round(float(total) / float(count), 2)}"
        return ""

    def _ridi_score(self, book):
        ratings = book.get("ratings") if isinstance(book, dict) else None
        if not isinstance(ratings, list):
            return ""
        count = 0
        total = 0
        for rating in ratings:
            if not isinstance(rating, dict):
                continue
            c = self._int(rating.get("count"), 0, 0, 100000000)
            r = self._int(rating.get("rating"), 0, 0, 5)
            count += c
            total += c * r
        if count:
            return f"{round(float(total) / float(count), 2)}"
        return ""

    def _is_adult(self, item):
        return bool(item.get("adult") or item.get("nineteen") or item.get("isAdult") or str(item.get("age", "")).startswith("19"))

    def _is_kakaopage_adult(self, item):
        return self._int(item.get("age_grade"), 0, 0, 99) >= 19

    def _as_list(self, value):
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for key in ("searchViewList", "list", "items", "contents"):
                if isinstance(value.get(key), list):
                    return value.get(key)
        return []

    def _sources(self, value):
        raw = [v.strip().lower() for v in (value or "all").split(",") if v.strip()]
        if not raw or "all" in raw:
            return set(self.SOURCE_ORDER)
        aliases = {
            "naver": "naver_webtoon",
            "series": "naver_series",
            "kakao": "kakao_webtoon",
            "page": "kakaopage",
            "ridi": "ridibooks",
            "ridibooks": "ridibooks",
        }
        return {aliases.get(v, v) for v in raw if aliases.get(v, v) in self.SOURCE_ORDER}

    def _dedupe(self, items):
        seen = set()
        result = []
        for item in items:
            key = item.get("link") or (item.get("publisher"), item.get("title"))
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    def _normalize(self, value):
        return re.sub(r"\s+", "", self._clean_text(value).lower())

    def _truthy(self, value):
        return str(value).strip().lower() in ("1", "true", "yes", "y", "on")

    def _int(self, value, default, min_value, max_value):
        try:
            value = int(value)
        except Exception:
            value = default
        return max(min_value, min(max_value, value))
