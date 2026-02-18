# cartoon-filter

`cartoon-filter` is an engineering project focused on building a cartoon-style image filter and comparing performance between C++ and x64 Assembly implementations inside one Windows solution.

The primary objective was educational and experimental: implement the same processing approach in C++ and ASM, integrate both into a C# desktop app, and use the project to study cross-language architecture, native interop, and optimization tradeoffs.

The project achieved that objective: both native paths were implemented and integrated, the application runs in x64 builds, and the full workflow (load image, tune `density`, apply filter, save output) works in a single executable environment.

From a software engineering perspective, the project delivered:
- A working cross-language architecture (`C# -> C++/ASM DLL`) with runtime integration.
- A functional image-processing pipeline for common formats (BMP/JPG/PNG).
- A practical setup for C++ vs ASM speed comparison and low-level optimization learning.

Simplified project structure:

```text
cartoon-filter/
|- GraphicFilter.sln
|- README.md
`- src/
   |- GraphicFilterPrototyp/   # C# WinForms app (.NET Framework 4.8)
   |- CppCode/                 # Native C++ DLL
   `- ASMCode/                 # x64 MASM DLL
```

Build and validation are centered on Visual Studio 2022 and the `x64` target. Build `GraphicFilter.sln` (Debug or Release), then run the generated artifacts from `bin\x64\<Configuration>\`.

```powershell
msbuild .\GraphicFilter.sln /t:Build /p:Configuration=Debug /p:Platform=x64
```

Requirements: Windows (x64), Visual Studio 2022 with C#/.NET desktop and C++ workloads, MASM build tools, and .NET Framework 4.8 runtime.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
