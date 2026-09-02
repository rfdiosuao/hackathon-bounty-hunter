#!/bin/bash
# ============================================================
# GitHub 国内加速一键配置脚本
# 用途：在云电脑/容器中配置 git 加速，避免 clone 中断
# 使用：bash setup-github-mirror.sh
# ============================================================
set -e

echo "=========================================="
echo "  GitHub 国内加速配置"
echo "=========================================="

# 主加速源（按优先级排序，第一个生效的会被使用）
MIRRORS=(
    "https://ghproxy.com/https://github.com/"
    "https://mirror.ghproxy.com/https://github.com/"
    "https://gh.llkk.cc/https://github.com/"
    "https://hub.gitmirror.com/https://github.com/"
)

# 测试每个加速源的连通性
SELECTED=""
for mirror in "${MIRRORS[@]}"; do
    echo -n "测试 $mirror ... "
    if curl -s --max-time 8 -o /dev/null -w "%{http_code}" "${mirror}https://github.com/git/git.git/info/refs?service=git-upload-pack" 2>/dev/null | grep -q "200\|301\|302"; then
        echo "OK"
        if [ -z "$SELECTED" ]; then
            SELECTED="$mirror"
        fi
    else
        echo "失败"
    fi
done

if [ -z "$SELECTED" ]; then
    echo ""
    echo "⚠️  所有加速源均不可达，回退到直连 GitHub"
    SELECTED="https://github.com/"
fi

echo ""
echo "✅ 选用加速源：$SELECTED"

# 配置 git insteadOf（全局生效）
git config --global url."${SELECTED}".insteadOf "https://github.com/"

# 配置 git 超时和重试
git config --global http.lowSpeedLimit 1000
git config --global http.lowSpeedTime 60
git config --global http.postBuffer 524288000

echo ""
echo "=========================================="
echo "  配置完成！"
echo "=========================================="
echo ""
echo "当前 git 配置："
git config --global --get-regexp 'url\..*insteadOf' || true
echo ""
echo "测试 clone（浅克隆）："
echo "  git clone --depth 1 https://github.com/git/git.git /tmp/git-test"
echo ""
echo "取消加速："
echo "  git config --global --unset url.\"${SELECTED}\".insteadOf"
