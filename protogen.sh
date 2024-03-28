#! /bin/bash
# script generates simtest/proto .py files out of simtest.proto

python3 -c "import grpc_tools" &> /dev/null
if [ $? -ne 0 ]; then
    echo "grpc_tools not installed. Hint: pip3 install -r requirements_dev.txt"
    exit 1
fi

ROOT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROTO_FILE="$ROOT_DIR/simtest.proto"
PROTO_OUT_DIR="$ROOT_DIR/simtest/proto"
PROTO_REFLECTION_OUT_DIR="$PROTO_OUT_DIR/reflection"
PROTO_GRPC_OUT_DIR="$PROTO_OUT_DIR/grpc"

mkdir -p "$PROTO_OUT_DIR" "$PROTO_REFLECTION_OUT_DIR" "$PROTO_GRPC_OUT_DIR"

python3 -m grpc_tools.protoc \
    -I "$ROOT_DIR" \
    --python_out="$PROTO_REFLECTION_OUT_DIR" \
    --python_betterproto_out="$PROTO_GRPC_OUT_DIR" \
    "$PROTO_FILE"

cat <<EOT > "$PROTO_OUT_DIR"/__init__.py
from . import reflection, grpc
EOT

cat <<EOT > "$PROTO_REFLECTION_OUT_DIR/__init__.py"
import os
import sys

pkg_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(pkg_dir)

from .simtest_pb2 import *
EOT
