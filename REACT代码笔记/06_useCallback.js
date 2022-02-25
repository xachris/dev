// REACT 代码笔记
// 主题: useCallback 待办事项, 避免重复渲染，附带 Todos.js
// 日期: 20220224

// 总结: 使用回调函数, 页面中未变化的组件不会重复被渲染

// PART 1 导入钩子
import { useState, useCallback } from "react";
import ReactDOM from "react-dom";
import Todos from "./Todos";                  // 导入自定义的 Todos组件


// PART 2 定义组件
const App = () => {

  const [count, setCount] = useState(0);      // 初始化状态 -- 计数器变量
  const [todos, setTodos] = useState([]);     // 初始化状态 -- 待办事项数组

  const increment = () => {                   // 函数 -- 计数器加1
    setCount((c) => c + 1);
  };

  const addTodo = useCallback(() => {         // 回调函数 -- 增加一个新待办事项
    setTodos((t) => [...t, "New Todo"]);      // 使用回调函数, 计数器加1时, Todos不会渲染
  }, [todos]);                                // Todos.js中的 console.log() 不会增加计数

  // const addTodo = () => {                     // 不使用回调函数, 
  //   setTodos((t) => [...t, "New Todo"]);      // Todos.js中的 console.log() 会增加计数
  // };

  return (                                    // 返回页面内容 -- 使用回调函数 嵌入Todos组件
    <>
      <Todos todos={todos} addTodo={addTodo} />
      <hr />
      <div>
        Count: {count}
        <button onClick={increment}>+</button>
      </div>
    </>
  );
};

// PART 3 渲染页面
ReactDOM.render(<App />, document.getElementById('root'));