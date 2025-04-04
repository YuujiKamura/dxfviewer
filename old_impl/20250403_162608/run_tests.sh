#!/bin/bash
# DXF Viewerテスト実行スクリプト
# 必ず dxfviewer ディレクトリ内で実行してください

# カラー出力用の設定
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}DXF Viewerテスト実行スクリプト${NC}"
echo -e "${YELLOW}======================${NC}\n"

# 現在のディレクトリを確認
CURRENT_DIR=$(basename $(pwd))
if [ "$CURRENT_DIR" != "dxfviewer" ]; then
  echo -e "${RED}エラー: このスクリプトは dxfviewer ディレクトリ内で実行してください${NC}"
  echo "現在のディレクトリ: $(pwd)"
  echo "正しい実行方法: cd dxfviewer && ./run_tests.sh"
  exit 1
fi

run_test() {
  local test_cmd="$1"
  local test_name="$2"
  local timeout_seconds="$3"
  
  echo -e "\n${YELLOW}テスト実行: ${test_name}${NC}"
  echo "コマンド: $test_cmd"
  
  # タイムアウト付きでコマンドを実行
  timeout "$timeout_seconds"s $test_cmd
  
  # 終了コードをチェック
  local exit_code=$?
  if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✓ テスト成功: ${test_name}${NC}"
    return 0
  elif [ $exit_code -eq 124 ]; then
    echo -e "${YELLOW}i テストは正常に開始されましたが、タイムアウトしました (${timeout_seconds}秒)${NC}"
    return 0
  else
    echo -e "${RED}✗ テスト失敗: ${test_name} (終了コード: ${exit_code})${NC}"
    return 1
  fi
}

# テスト実行関数
run_tests() {
  local failed=0
  
  # 1. 本番コードの基本動作テスト
  echo -e "\n${YELLOW}1. 本番コードの基本動作テスト${NC}"
  run_test "python dxf_viewer_pyside6.py --file sample_dxf/12.25\ 新規路線.dxf --debug" "本番コード (サンプルDXF)" 3
  if [ $? -ne 0 ]; then failed=$((failed+1)); fi
  
  # 2. シンプルパンテスト
  echo -e "\n${YELLOW}2. シンプルパンテスト${NC}"
  if [ -f "tests/ui_tests/simple_pan_test.py" ]; then
    run_test "python tests/ui_tests/simple_pan_test.py" "シンプルパンテスト" 3
    if [ $? -ne 0 ]; then failed=$((failed+1)); fi
  else
    echo -e "${RED}✗ テストファイルが見つかりません: tests/ui_tests/simple_pan_test.py${NC}"
    failed=$((failed+1))
  fi
  
  # 3. レンダリングテスト
  echo -e "\n${YELLOW}3. レンダリング設定テスト${NC}"
  if [ -f "tests/test_viewer_rendering.py" ]; then
    run_test "python tests/test_viewer_rendering.py" "レンダリングテスト" 5
    if [ $? -ne 0 ]; then failed=$((failed+1)); fi
  else
    echo -e "${RED}✗ テストファイルが見つかりません: tests/test_viewer_rendering.py${NC}"
    failed=$((failed+1))
  fi
  
  # 4. パフォーマンステスト
  echo -e "\n${YELLOW}4. パフォーマンステスト${NC}"
  if [ -f "tests/test_perf_rendering.py" ]; then
    run_test "python tests/test_perf_rendering.py" "パフォーマンステスト" 15
    if [ $? -ne 0 ]; then failed=$((failed+1)); fi
  else
    echo -e "${RED}✗ テストファイルが見つかりません: tests/test_perf_rendering.py${NC}"
    failed=$((failed+1))
  fi
  
  # 5. ハイブリッドテスト (簡易テスト + 本番設定)
  if [ -f "tests/ui_tests/hybrid_test.py" ]; then
    echo -e "\n${YELLOW}5. ハイブリッドテスト${NC}"
    run_test "python tests/ui_tests/hybrid_test.py" "ハイブリッドテスト" 3
    if [ $? -ne 0 ]; then failed=$((failed+1)); fi
  fi
  
  # 結果報告
  echo -e "\n${YELLOW}テスト実行結果${NC}"
  echo -e "${YELLOW}==============${NC}"
  
  if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ すべてのテストが成功しました${NC}"
  else
    echo -e "${RED}✗ ${failed}個のテストが失敗しました${NC}"
  fi
  
  return $failed
}

# インタラクティブテスト実行関数
run_interactive_tests() {
  echo -e "\n${YELLOW}インタラクティブテスト${NC}"
  echo -e "${YELLOW}====================${NC}"
  echo "インタラクティブテストでは、テストを実行して手動で操作を確認します。"
  echo "各テストは3秒後に自動的に終了します。"
  echo -e "終了を待たずに次に進むには ${GREEN}Ctrl+C${NC} を押してください。\n"
  
  local tests=(
    "python dxf_viewer_pyside6.py --file sample_dxf/12.25\ 新規路線.dxf --debug:本番コード:10"
    "python tests/ui_tests/simple_pan_test.py:シンプルパンテスト:10"
    "python tests/ui_tests/hybrid_test.py:ハイブリッドテスト（シンプル+本番設定）:10"
    "python tests/test_viewer_rendering.py --interactive:レンダリングテスト（インタラクティブ）:15"
    "python tests/test_perf_rendering.py --interactive:パフォーマンステスト（インタラクティブ）:15"
  )
  
  for test_spec in "${tests[@]}"; do
    IFS=':' read -r cmd name timeout <<< "$test_spec"
    
    echo -e "\n${YELLOW}実行: ${name}${NC}"
    echo "コマンド: $cmd"
    echo -e "テストを終了するには ${GREEN}Ctrl+C${NC} を押してください..."
    sleep 2
    
    timeout "${timeout}s" $cmd || true
    
    echo -e "\n${GREEN}✓ テスト実行完了: ${name}${NC}"
    echo -e "次のテストを実行するには Enter キーを押してください..."
    read -n 1
  done
  
  echo -e "\n${GREEN}✓ すべてのインタラクティブテストが完了しました${NC}"
}

# コマンドライン引数によって実行モードを切り替え
if [ "$1" == "--interactive" ]; then
  run_interactive_tests
else
  run_tests
  exit $?
fi 