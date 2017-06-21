# crowdserver
Server infrastructure for crowd tasks

## TODO

1. Integrate static tasks into crowd server
2. Add task indices / hierarchy
  * A single target (e.g. a frame) may involve multiple tasks (segment, evaluate, scribble ...)
  * A full project contains many targets (sequences, frames ...)
3. Add task submit
  * Upload result, then forward to next (mturk, task, index ...)
  * Carry task parameters (assignmentId, workerId ...) through sessions
4. Add task processing and composition
  * Some tasks depend on the result of others
  * Finishing a task may generate new tasks
