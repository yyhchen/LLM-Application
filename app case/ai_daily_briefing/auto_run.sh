#!/bin/bash

# AI日报自动生成和查看脚本 (Shell版本)
# 功能: 运行 ai_daily_news.py 并启动 Live Server 查看 reading.html

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 获取当前日期 (YYYY_MM_DD 格式)
get_current_date() {
    date +"%Y_%m_%d"
}

# 检查文件是否存在
check_files() {
    local current_date=$(get_current_date)
    local json_file="${current_date}.json"
    local txt_file="${current_date}_news_data.txt"
    
    print_info "检查当天数据文件..."
    
    if [[ -f "$json_file" && -f "$txt_file" ]]; then
        print_success "数据文件已存在: $json_file, $txt_file"
        return 0
    else
        print_warning "数据文件不存在或不完整"
        return 1
    fi
}

# 运行 ai_daily_news.py
run_ai_daily_news() {
    print_info "运行 ai_daily_news.py..."
    
    if python3 ai_daily_news.py; then
        print_success "ai_daily_news.py 运行完成"
        return 0
    else
        print_error "ai_daily_news.py 运行失败"
        return 1
    fi
}

# 启动 Live Server
start_live_server() {
    print_info "启动 Live Server..."
    
    # 检查 live-server 是否安装
    if command -v live-server &> /dev/null; then
        print_success "使用 live-server 启动..."
        live-server --open=reading.html &
        return 0
    elif command -v npx &> /dev/null; then
        print_success "使用 npx live-server 启动..."
        npx live-server --open=reading.html &
        return 0
    else
        print_error "未找到 Live Server"
        print_warning "请安装: npm install -g live-server"
        
        # 尝试用默认浏览器打开
        local html_path="$(pwd)/reading.html"
        if command -v open &> /dev/null; then
            # macOS
            print_info "尝试用默认浏览器打开..."
            open "file://$html_path"
        elif command -v xdg-open &> /dev/null; then
            # Linux
            print_info "尝试用默认浏览器打开..."
            xdg-open "file://$html_path"
        else
            print_warning "请手动打开: file://$html_path"
        fi
        return 1
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "🤖 AI日报自动生成和查看工具"
    echo "=========================================="
    
    # 切换到脚本所在目录
    cd "$(dirname "$0")"
    print_info "当前目录: $(pwd)"
    
    # 检查必要文件
    if [[ ! -f "ai_daily_news.py" ]]; then
        print_error "未找到 ai_daily_news.py 文件"
        exit 1
    fi
    
    if [[ ! -f "reading.html" ]]; then
        print_error "未找到 reading.html 文件"
        exit 1
    fi
    
    # 检查文件是否已存在
    if check_files; then
        read -p "📝 数据文件已存在，是否重新生成? (y/N): " choice
        case "$choice" in 
            y|Y|yes|YES ) 
                print_info "重新生成数据..."
                if ! run_ai_daily_news; then
                    print_error "数据生成失败"
                    exit 1
                fi
                ;;
            * ) 
                print_info "跳过数据生成..."
                ;;
        esac
    else
        print_info "开始生成当天数据..."
        if ! run_ai_daily_news; then
            print_error "数据生成失败"
            exit 1
        fi
    fi
    
    # 再次检查文件
    if ! check_files; then
        print_error "数据文件生成失败!"
        exit 1
    fi
    
    # 启动 Live Server
    echo "=========================================="
    start_live_server
    
    print_success "设置完成!"
    print_info "你现在可以在浏览器中查看今天的AI日报了"
    print_warning "按 Ctrl+C 停止脚本"
    
    # 等待用户中断
    trap 'echo -e "\n👋 程序已停止"; exit 0' INT
    while true; do
        sleep 1
    done
}

# 运行主函数
main "$@"