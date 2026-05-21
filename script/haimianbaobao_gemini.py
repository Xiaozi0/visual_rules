import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import json
import os

# ==========================================
# 1. 核心逻辑引擎：空间推导与状态机
# ==========================================
class RollingCubeSimulator:
    def __init__(self, top, bottom, front, back, left, right, x=0, y=0):
        self.state = {
            "top": top, "bottom": bottom, "front": front,
            "back": back, "left": left, "right": right
        }
        self.x = x
        self.y = y

    def get_grid_color(self):
        # (0,0) 设为黑格，奇偶性判断
        return "Black" if (self.x + self.y) % 2 == 0 else "White"

    def move(self, direction):
        top, bottom, front, back = self.state["top"], self.state["bottom"], self.state["front"], self.state["back"]
        left, right = self.state["left"], self.state["right"]
        
        if direction in ["Up", "Forward", "North"]: # +y
            self.state.update({"top": front, "back": top, "bottom": back, "front": bottom})
            self.y += 1
        elif direction in ["Down", "Backward", "South"]: # -y
            self.state.update({"top": back, "front": top, "bottom": front, "back": bottom})
            self.y -= 1
        elif direction in ["Left", "West"]: # -x
            self.state.update({"top": right, "left": top, "bottom": left, "right": bottom})
            self.x -= 1
        elif direction in ["Right", "East"]: # +x
            self.state.update({"top": left, "right": top, "bottom": right, "left": bottom})
            self.x += 1

# ==========================================
# 2. 视觉渲染引擎：生成带坐标轴的 3D 图像
# ==========================================
def render_3d_puzzle(cube_x, cube_y, face_labels, filename):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_box_aspect([1, 1, 0.5]) 
    
    # 绘制 4x4 棋盘
    board_size = 4
    for i in range(-1, board_size):
        for j in range(-1, board_size):
            color = '#333333' if (i + j) % 2 == 0 else '#EEEEEE'
            X, Y, Z = [i, i+1, i+1, i], [j, j, j+1, j+1], [0, 0, 0, 0]
            verts = [list(zip(X, Y, Z))]
            ax.add_collection3d(Poly3DCollection(verts, color=color, alpha=0.9))

    # 绘制坐标系指示器 (消除方向歧义)
    # 将指示器放在棋盘的左下角外侧 (-1.5, -1.5)
    ax.quiver(-1.5, -1.5, 0, 1.5, 0, 0, color='red', arrow_length_ratio=0.15, linewidths=2)
    ax.text(0.2, -1.5, 0, 'Right (+x)', color='red', fontweight='bold')
    ax.quiver(-1.5, -1.5, 0, 0, 1.5, 0, color='green', arrow_length_ratio=0.15, linewidths=2)
    ax.text(-1.5, 0.2, 0, 'Up (+y)', color='green', fontweight='bold')

    # 计算方块顶点
    z_base = 0
    v = np.array([
        [cube_x, cube_y, z_base], [cube_x+1, cube_y, z_base], 
        [cube_x+1, cube_y+1, z_base], [cube_x, cube_y+1, z_base],
        [cube_x, cube_y, z_base+1], [cube_x+1, cube_y, z_base+1], 
        [cube_x+1, cube_y+1, z_base+1], [cube_x, cube_y+1, z_base+1]
    ])
    
    # 定义面和颜色映射 (模拟视觉特征)
    faces = [
        [v[0], v[1], v[2], v[3]], # Bottom
        [v[4], v[5], v[6], v[7]], # Top
        [v[0], v[1], v[5], v[4]], # Front
        [v[2], v[3], v[7], v[6]], # Back
        [v[0], v[3], v[7], v[4]], # Left
        [v[1], v[2], v[6], v[5]]  # Right
    ]
    
    color_map = {
        "Brown Pants": "saddlebrown", "SpongeBob Face": "gold", 
        "White Shoes": "whitesmoke", "Back of Head": "khaki", 
        "Left Arm": "gold", "Right Arm": "gold"
    }
    
    colors = [
        color_map.get(face_labels["bottom"], "gray"), color_map.get(face_labels["top"], "gray"),
        color_map.get(face_labels["front"], "gray"), color_map.get(face_labels["back"], "gray"),
        color_map.get(face_labels["left"], "gray"), color_map.get(face_labels["right"], "gray")
    ]
    
    labels = ["", face_labels["top"], face_labels["front"], "", "", face_labels["right"]]

    for i in range(6):
        poly = Poly3DCollection([faces[i]], color=colors[i], edgecolors='k', linewidths=1.5)
        ax.add_collection3d(poly)
        if labels[i]:
            center = np.mean(faces[i], axis=0)
            ax.text(center[0], center[1], center[2] + 0.05, labels[i], 
                    color='black', ha='center', va='center', fontweight='bold', fontsize=9)

    ax.set_xlim([-2, board_size])
    ax.set_ylim([-2, board_size])
    ax.set_zlim([0, 3])
    ax.axis('off')
    ax.view_init(elev=35, azim=-45) # 经典等轴视角
    
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', dpi=150)
    plt.close()

# ==========================================
# 3. 数据集装配：严格遵守 vis_scaling 格式
# ==========================================
def build_vis_scaling_dataset(configs, output_json="vis_scaling_simple_mm.json", img_dir="images"):
    # 创建图片目录
    os.makedirs(img_dir, exist_ok=True)
    dataset = []
    
    for idx, config in enumerate(configs):
        # --- 步骤 A: 渲染图片 ---
        img_filename = f"{str(idx).zfill(5)}.png"
        img_filepath = os.path.join(img_dir, img_filename)
        render_3d_puzzle(
            cube_x=config.get("initial_pos", [0,0])[0], 
            cube_y=config.get("initial_pos", [0,0])[1], 
            face_labels=config["initial_orientation"], 
            filename=img_filepath
        )
        print(f"🎨 Generated Image: {img_filepath}")

        # --- 步骤 B: 跑逻辑引擎推导 GT (Ground Truth) ---
        cube = RollingCubeSimulator(
            top=config["initial_orientation"]["top"],
            bottom=config["initial_orientation"]["bottom"],
            front=config["initial_orientation"]["front"],
            back=config["initial_orientation"]["back"],
            left=config["initial_orientation"]["left"],
            right=config["initial_orientation"]["right"],
            x=config.get("initial_pos", [0,0])[0],
            y=config.get("initial_pos", [0,0])[1]
        )
        
        for direction in config["path"]:
            cube.move(direction)
            
        final_color = cube.get_grid_color()
        derived_answer = config.get("expected_answer", cube.state['top'])

        # --- 步骤 C: 构建 JSON ---
        difficulty = config.get("difficulty", "easy")
        family = config.get("family", "r_rolling_puzzle")
        slug = f"{family}_{difficulty}"
        
        # 统一相对路径格式 (如 "images/00000.png")
        media_path = f"{img_dir}/{img_filename}"
        
        sample = {
            "id": config.get("task_id", f"{slug}-0-{str(idx).zfill(5)}"),
            "media": [media_path],
            "messages": [
                {
                    "role": "user",
                    "question": f"<image> {config['question']}",
                    "answer": "",
                    "options": {},
                    "choices": [],
                    "hint": ""
                }
            ],
            "metadata": {
                "dataset": {
                    "slug": slug,
                    "source_id": "99_r_rolling_puzzle",
                    "family": family,
                    "upstream_name": difficulty,
                    "title": f"Rule-Based Rolling Puzzle: {difficulty.capitalize()}"
                },
                "gt": {
                    "answer": derived_answer,
                    "answer_type": config.get("answer_type", "string"),
                    "choices": [],
                    "validator": {
                        "kind": config.get("validator_kind", "exact_match"),
                        "solution": derived_answer
                    }
                },
                "provenance": {
                    "seed": 0,
                    "index": idx,
                    "generator": "rule_based_python",
                    "rule_source": "vendor/rule-based/rolling_puzzle/rules.md"
                },
                "instance": {
                    "initial_pos": config.get("initial_pos", [0, 0]),
                    "initial_orientation": config["initial_orientation"],
                    "path": config["path"],
                    "difficulty": difficulty,
                    "final_state_debug": {
                        "coordinate": [cube.x, cube.y],
                        "color": final_color,
                        "orientation": cube.state
                    }
                }
            }
        }
        dataset.append(sample)
        
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Successfully generated {len(dataset)} samples into '{output_json}'!")

# ==========================================
# 4. 题目配置库 (全英文输入)
# ==========================================
if __name__ == "__main__":
    task_configs = [
        {
            "difficulty": "easy",
            "initial_pos": [0, 0],
            "initial_orientation": {
                "top": "Brown Pants", "bottom": "White Shoes", "front": "SpongeBob Face",
                "back": "Back of Head", "left": "Left Arm", "right": "Right Arm"
            },
            "path": ["Right", "Up", "Right"],
            "question": "Note the red and green coordinate arrows in the image. The cube is currently at (0,0). If it rolls sequentially 'Right', 'Up', and 'Right', what will its top face be? Return only the face name.",
            "expected_answer": "SpongeBob Face",
            "answer_type": "string",
            "validator_kind": "exact_string"
        },
        {
            "difficulty": "hard",
            "initial_pos": [0, 0],
            "initial_orientation": {
                "top": "Brown Pants", "bottom": "White Shoes", "front": "SpongeBob Face",
                "back": "Back of Head", "left": "Left Arm", "right": "Right Arm"
            },
            "path": [], 
            "question": "The image displays a spatial puzzle. Is it possible to perform a sequence of grid rolls to keep the cube on its current starting square, but have the 'SpongeBob Face' pointing upwards? Answer 'Yes' or 'No'.",
            "expected_answer": "No",
            "answer_type": "string",
            "validator_kind": "exact_string"
        }
    ]

    build_vis_scaling_dataset(task_configs)