// REACT 代码笔记
// 主题: useRef 记录文本框输入
// 日期: 20220223

// 总结: 使用useRef不会导致页面被再次渲染, 从而提升性能

// PART 1 导入钩子
import { useState, useEffect, useRef } from "react";
import ReactDOM from "react-dom";


// PART 2 定义组件
function App() {

  // 初始化用户输入文本为空
  const [inputValue, setInputValue] = useState("");
  // 初始化此前输入文本为空
  const previousInputValue = useRef("");

  // 设计渲染后附加效果 -- 输入产生变化后, 此前输入文本更新为现输入文本
  useEffect(() => {
    previousInputValue.current = inputValue;
  }, [inputValue]);

  // 页面内容呈现
  return (
    <>
    {/* 输入文本框 */}
      <input
        type="text"
        value={inputValue}
        // 当文本框内容改变, 则更新文本框显示内容 inputValue
        onChange={(e) => setInputValue(e.target.value)}
      />

      {/* 页面显示当前文本内容 */}
      <h2>Current Value: {inputValue}</h2>

      {/* 页面显示此前文本内容 */}
      <h2>Previous Value: {previousInputValue.current}</h2>
    </>
  );
}


// PART 3 渲染页面
ReactDOM.render(<App />, document.getElementById('root'));