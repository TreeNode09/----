from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension
import os

# 硬编码您的CUDA安装路径
cuda_home = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6"

setup(
    name='my_interp',
    ext_modules=[
        CUDAExtension('my_interp', [
            'my_interp_cuda.cpp',
            'my_interp_cuda_kernel.cu',
        ]),
    ],
    cmdclass={
        'build_ext': BuildExtension
    })
