# AI Trust Check 발표자료

`index.html`은 reveal.js 5.1.0을 `assets/`에 포함하므로 인터넷 연결 없이도 실행됩니다.

## 로컬 발표

```bash
cd presentation
python3 -m http.server 8000
```

브라우저에서 <http://localhost:8000>을 엽니다. 방향키로 이동하고, `F`로 전체화면, `S`로 발표자 노트를 엽니다.

## PDF 백업

Chrome에서 아래 주소를 열어 PDF로 인쇄합니다.

```text
http://localhost:8000/?print-pdf
```

인쇄 대화상자에서 **배경 그래픽**을 켜고 **PDF로 저장**을 선택합니다. fragment를 한 장에 합쳐 출력하도록 설정되어 있습니다.

## GitHub Pages

`.github/workflows/pages.yml`은 `main` 브랜치에 push될 때 `presentation/`만 Pages artifact로 업로드합니다. GitHub 저장소의 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 설정해야 합니다.
