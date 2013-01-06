@echo off
for %%f in (.\*.ui) do (
	call ui2py.bat %%f
)