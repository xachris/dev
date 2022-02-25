// REACT 代码笔记
// 主题: useMeno 待办事项, 避免重复渲染，
// 日期: 20220224

// 总结: 使用 useMemo, 页面中未变化的值不会重复被渲染

// PART 1 导入钩子
import { useState, useMemo } from "react";
import ReactDOM from "react-dom";


// PART 2 定义组件
const App = () => {

  // 初始化 计数器, 待办事项, 计算结果(使用useMemo避免重复渲染, 需要添加触发条件数组) 
  const [count, setCount] = useState(0);
  const [todos, setTodos] = useState([]);
  const calculation = useMemo(() => expensiveCalculation(count), [count]);
  // const calculation = expensiveCalculation(count);      // 未使用useMemo()则会重复渲染

  const increment = () => {                                // 定义函数 -- 数字加1
    setCount((c) => c + 1);
  };

  const addTodo = () => {                                  // 定义函数 -- 待办事项加一条记录
    setTodos((t) => [...t, "New Todo"]);
  };

  return (                              // 返回页面内容 -- 映射每条待办记录, 点击按钮添加记录
                                        // 点击加号按钮计数器加1, 计数器数值变化联导引发巨量计算
    <div>
      <div>
        <h2>My Todos</h2>
        {todos.map((todo, index) => {
          return <p key={index}>{todo}</p>;
        })}
        <button onClick={addTodo}>Add Todo</button>
      </div>
      <hr />
      <div>
        Count: {count}
        <button onClick={increment}>+</button>
        <h2>Expensive Calculation</h2>
        {calculation}
      </div>
    </div>
  );
};


const expensiveCalculation = (num) => {               // 巨大耗时运算函数(10亿次)
  console.log("Calculating...");
  for (let i = 0; i < 1000000000; i++) {
    num += 1;
  }
  return num;
};


// PART 3 渲染页面
ReactDOM.render(<App />, document.getElementById("root"));