#!/usr/bin/env python3
"""
测试Bulma样式更新
验证现货交易控制面板和合约交易控制面板的样式是否正确应用
"""

import requests
import time

def test_bulma_styles():
    """测试Bulma样式更新"""
    print("🧪 测试Bulma样式更新...")
    print("=" * 50)

    base_url = "http://localhost:5000"
    
    try:
        # 1. 测试现货交易页面
        print("1️⃣ 测试现货交易页面...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ 现货交易页面加载成功")
            
            # 检查是否包含Bulma CSS
            if "bulma@1.0.4" in response.text:
                print("✅ Bulma CSS框架已正确引入")
            else:
                print("❌ Bulma CSS框架未找到")
                
            # 检查是否包含Bootstrap（应该被移除）
            if "bootstrap" in response.text.lower():
                print("⚠️  发现Bootstrap引用，应该已被移除")
            else:
                print("✅ Bootstrap已成功移除")
        else:
            print(f"❌ 现货交易页面加载失败: {response.status_code}")
            return

        # 2. 测试合约交易页面
        print("\n2️⃣ 测试合约交易页面...")
        response = requests.get(f"{base_url}/futures")
        if response.status_code == 200:
            print("✅ 合约交易页面加载成功")
            
            # 检查是否包含Bulma CSS
            if "bulma@1.0.4" in response.text:
                print("✅ Bulma CSS框架已正确引入")
            else:
                print("❌ Bulma CSS框架未找到")
                
            # 检查是否包含Bootstrap（应该被移除）
            if "bootstrap" in response.text.lower():
                print("⚠️  发现Bootstrap引用，应该已被移除")
            else:
                print("✅ Bootstrap已成功移除")
        else:
            print(f"❌ 合约交易页面加载失败: {response.status_code}")
            return

        # 3. 检查关键Bulma类名
        print("\n3️⃣ 检查关键Bulma类名...")
        
        # 现货页面检查
        response = requests.get(f"{base_url}/")
        content = response.text
        
        bulma_classes = [
            "navbar is-primary",
            "section",
            "container",
            "columns",
            "column",
            "card",
            "card-header",
            "card-content",
            "button is-success",
            "button is-danger",
            "button is-info",
            "table is-fullwidth",
            "notification is-info",
            "tag is-danger",
            "tag is-light",
            "modal",
            "modal-card",
            "modal-card-head",
            "modal-card-body",
            "modal-card-foot"
        ]
        
        found_classes = []
        missing_classes = []
        
        for class_name in bulma_classes:
            if class_name in content:
                found_classes.append(class_name)
            else:
                missing_classes.append(class_name)
        
        print(f"✅ 找到的Bulma类名: {len(found_classes)}/{len(bulma_classes)}")
        for class_name in found_classes:
            print(f"   ✓ {class_name}")
            
        if missing_classes:
            print(f"❌ 缺失的Bulma类名: {len(missing_classes)}")
            for class_name in missing_classes:
                print(f"   ✗ {class_name}")

        # 检查表格样式
        if "table is-fullwidth is-striped" in content:
            print("   ✓ table is-fullwidth is-striped (组合类名)")
        else:
            print("   ✗ table is-fullwidth is-striped (组合类名)")

        # 4. 检查合约页面
        print("\n4️⃣ 检查合约页面Bulma类名...")
        response = requests.get(f"{base_url}/futures")
        content = response.text
        
        futures_bulma_classes = [
            "navbar is-warning",
            "box has-background-warning-light",
            "title is-4",
            "buttons",
            "select is-fullwidth"
        ]
        
        found_futures_classes = []
        missing_futures_classes = []
        
        for class_name in futures_bulma_classes:
            if class_name in content:
                found_futures_classes.append(class_name)
            else:
                missing_futures_classes.append(class_name)
        
        print(f"✅ 找到的合约页面Bulma类名: {len(found_futures_classes)}/{len(futures_bulma_classes)}")
        for class_name in found_futures_classes:
            print(f"   ✓ {class_name}")
            
        if missing_futures_classes:
            print(f"❌ 缺失的合约页面Bulma类名: {len(missing_futures_classes)}")
            for class_name in missing_futures_classes:
                print(f"   ✗ {class_name}")

        # 检查多选下拉框
        if "select is-fullwidth is-multiple" in content:
            print("   ✓ select is-fullwidth is-multiple (组合类名)")
        else:
            print("   ✗ select is-fullwidth is-multiple (组合类名)")

        # 5. 检查模态框
        print("\n5️⃣ 检查模态框结构...")
        
        modal_structures = [
            "modal-background",
            "modal-card",
            "modal-card-head",
            "modal-card-body",
            "modal-card-foot",
            "delete"
        ]
        
        found_modals = []
        missing_modals = []
        
        for modal_part in modal_structures:
            if modal_part in content:
                found_modals.append(modal_part)
            else:
                missing_modals.append(modal_part)
        
        print(f"✅ 找到的模态框结构: {len(found_modals)}/{len(modal_structures)}")
        for modal_part in found_modals:
            print(f"   ✓ {modal_part}")
            
        if missing_modals:
            print(f"❌ 缺失的模态框结构: {len(missing_modals)}")
            for modal_part in missing_modals:
                print(f"   ✗ {modal_part}")

        print("\n🎉 Bulma样式更新测试完成!")
        print("\n📋 总结:")
        print(f"   • 现货页面: {'✅ 成功' if len(found_classes) > len(bulma_classes) * 0.8 else '❌ 需要检查'}")
        print(f"   • 合约页面: {'✅ 成功' if len(found_futures_classes) > len(futures_bulma_classes) * 0.8 else '❌ 需要检查'}")
        print(f"   • 模态框: {'✅ 成功' if len(found_modals) > len(modal_structures) * 0.8 else '❌ 需要检查'}")
        
        print("\n🌐 访问地址:")
        print(f"   • 现货交易: {base_url}/")
        print(f"   • 合约交易: {base_url}/futures")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_bulma_styles()
