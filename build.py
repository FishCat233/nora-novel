# build.py
import subprocess
import sys
import os
import argparse


def get_git_version(use_commit_hash=False):
    """获取 Git 版本：优先 tag，否则 commit hash"""
    try:
        if use_commit_hash:
            # 获取短 commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        else:
            # 获取最近 tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # 无 tag，回退到 commit hash
                print("警告：未找到 tag，使用 commit hash", file=sys.stderr)
                result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"错误：无法获取版本信息 - {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("错误：未安装 Git 或不在 Git 仓库中", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="根据 Git 版本构建 Docker 镜像")
    parser.add_argument(
        "--image", default="nora-novel", help="镜像名称，默认 nora-novel"
    )
    parser.add_argument("--path", default=".", help="Dockerfile 所在路径，默认当前目录")
    parser.add_argument(
        "--use-commit", action="store_true", help="使用 commit hash 而非 tag"
    )
    args = parser.parse_args()

    # 检查是否为 Git 仓库
    if not os.path.isdir(".git"):
        print("错误：当前目录不是一个 Git 仓库", file=sys.stderr)
        sys.exit(1)

    version = get_git_version(args.use_commit)
    print(f"当前版本：{version}")

    tag = f"{args.image}:{version}"
    print(f"开始构建镜像：{tag}")

    # 构建命令
    dockerfile = os.path.join(args.path, "Dockerfile")
    cmd = ["docker", "build", "-t", tag, "-f", dockerfile, args.path]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"构建成功！镜像：{tag}")
    else:
        print("构建失败", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
