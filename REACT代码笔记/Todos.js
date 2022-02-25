// REACT 代码笔记
// 主题: useCallback 待办事项, 避免重复渲染，附带 Todos.js
// 日期: 20220224


// 导入 memo 模块, 用于记忆重复内容, 从而避免重复渲染
import { memo } from "react";

// 定义组件 -- 传入状态
const Todos = ({ todos, addTodo }) => {       // 传入自定义的 todos属性, addTodo属性

  console.log("child render");                // 控制台记录, 表示是另一组件的子组件, 用于测试

  return (                                    // 返回页面内容, 映射每个 todos数组内的元素, 
    <>
      <h2>My Todos</h2>
      {todos.map((todo, index) => {
        return <p key={index}>{todo}</p>;
      })}
      <button onClick={addTodo}>Add Todo</button>
    </>
  );
};


// 默认导出 意在不重复渲染页面的 Todos 组件
export default memo(Todos);