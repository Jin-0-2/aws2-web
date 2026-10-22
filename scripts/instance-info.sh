#!/bin/bash
# EC2 메타데이터(IMDSv2)에서 인스턴스 이름과 사설 IP를 읽어 화면 왼쪽 아래 표시용 instance.json을 만든다.
# 사용: sudo bash scripts/instance-info.sh [저장 위치, 기본 /var/www/html/instance.json]
# 이름은 Name 태그를 쓰고, 인스턴스 메타데이터의 태그 허용이 꺼져 있으면 인스턴스 ID를 쓴다.
OUT=${1:-/var/www/html/instance.json}
MD=http://169.254.169.254/latest
TOKEN=$(curl -s -X PUT "$MD/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
get() { curl -sf -H "X-aws-ec2-metadata-token: $TOKEN" "$MD/meta-data/$1"; }

NAME=$(get tags/instance/Name || get instance-id)
IP=$(get local-ipv4)
printf '{"name":"%s","ip":"%s"}\n' "$NAME" "$IP" > "$OUT"
chmod 644 "$OUT"
cat "$OUT"
