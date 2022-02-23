// REACT 代码笔记
// 主题: useEffect 计时器
// 日期: 20220223


// PART 1 导入钩子
import { useState, useEffect } from "react";
import ReactDOM from "react-dom";


// PART 2 定义组件
function Timer() {

  // 初始化计数器
  const [count, setCount] = useState(0);

  // 设置渲染附带效果
  useEffect(() => {
    let timer = setTimeout(() => {          // 设置计次加1, 并间隔1秒后执行
    setCount((count) => count + 1);
  }, 1000);

  return () => clearTimeout(timer)          // 执行后常规清理执行函数 (重要!)
  }, []);                                   // 设置触发条件为空 (重要! 若不传入[]变量则会无限循环)

  return <h1>I've rendered {count} times!</h1>;     // 页面文字
}


// PART 3 渲染页面
ReactDOM.render(<Timer />, document.getElementById("root"));