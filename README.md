# aws2-web

동물병원 진료 관리 시스템의 웹(화면) 파일입니다. Apache에 올려서 사용합니다.

**코드는 수정할 필요가 없습니다.** 파일을 Apache에 복사하고, `/api/` 요청을 WAS 앞의 ALB로 보내는 리버스 프록시 설정만 추가하면 됩니다.

```
브라우저 ── /        → Apache가 이 저장소의 파일(index.html, *.js, *.css)을 그대로 제공
        └─ /api/... → Apache가 WAS 쪽 ALB로 전달 (/api는 떼고 전달)
```

## 1. 파일 복사

이 저장소의 파일을 Apache의 DocumentRoot(기본 `/var/www/html/`)에 바로 넣습니다. 폴더째 넣지 말고 파일만 넣으세요.

```bash
sudo cp index.html style.css api.js desk.js vet.js app.js /var/www/html/
```

### (선택) 화면에 인스턴스 이름 · 사설 IP 표시

웹 서버 인스턴스에서 아래 스크립트를 실행하면 `/var/www/html/instance.json`이 만들어지고, 모든 화면 왼쪽 아래에 `인스턴스이름 · 사설IP`가 표시됩니다. 파일이 없으면 표시되지 않습니다.

```bash
sudo bash scripts/instance-info.sh
```

- 이름은 인스턴스의 `Name` 태그를 씁니다. 태그를 읽으려면 EC2 인스턴스 설정에서 **인스턴스 메타데이터의 태그 허용**을 켜야 하고, 꺼져 있으면 인스턴스 ID가 표시됩니다.
- 시작 템플릿(오토스케일링)을 쓰면 사용자 데이터(user data)에 이 스크립트 내용을 넣어 두세요.
- `rsync --delete`로 배포하면 `instance.json`이 지워지니, 배포 후 다시 실행하세요.

## 2. 리버스 프록시 설정 (ALB 주소만 바꾸면 됨)

`/etc/httpd/conf.d/proxy.conf` 파일을 만들고 `내부ALB주소`를 실제 WAS ALB의 DNS 이름으로 바꿉니다.

```apache
ProxyPass        /api/ http://내부ALB주소/ disablereuse=On
ProxyPassReverse /api/ http://내부ALB주소/
ProxyTimeout 30
```

- `/api/`와 ALB 주소 끝에 `/`를 **둘 다** 붙여야 `/api`가 떼어지고 전달됩니다.
- `disablereuse=On`은 ALB IP가 바뀌어도 접속이 끊기지 않게 해 줍니다.

```bash
sudo apachectl configtest      # Syntax OK 확인
sudo systemctl reload httpd
```

## 확인

- `http://웹서버주소/` 접속 → 로그인 화면이 뜨면 정상입니다.
- 로그인이 안 되고 `/api/...` 요청이 502/503이면 ALB 주소, 보안 그룹(웹 서버 → ALB), SELinux(`sudo setsebool -P httpd_can_network_connect 1`)를 확인하세요.
