# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
from os import path
from logging import getLogger
from logging import getLogger, basicConfig, DEBUG
from sys import stderr
import time
from threading import Timer, Thread

from Queue import Queue, Empty

from migrate_tool.filter import Filter

logger = getLogger(__name__)


class BaseMigrator(object):

    def start(self):
        pass

    def stop(self):
        pass

    @property
    def status(self):
        """ Query migrate status

        :return: dict like {'success': 213, 'failure': 19, 'state': 'running'}
        """
        pass


class ThreadMigrator(BaseMigrator):
    """migrator Class, consisted of:
        1. Workers
        2. InputStorageService
        3. OutputStorageService
        4. Filter: Determines whether the file has been moved

    """

    def __init__(self, input_service, output_service, work_dir=None, threads=10, share_q=None, *args, **kwargs):

        self._input_service = input_service
        self._output_service = output_service

        self._work_dir = work_dir or os.getcwd()
        self._filter = Filter(self._work_dir)

        self._stop = False
        self._finish = False
        self._threads = []

        self._sleep_seconds = 6
        self._max_task_queue_size = 1000

        self._restore_prefix = 'restore_'
        self._max_restore_check_queue_size = 1000
        
        # todo, set maxsize to 0
        self._restore_check_queue = Queue(maxsize=0)

        # running task queue between multi processes
        self._task_queue = share_q

    def restore_thread(self):
        assert self._output_service is not None
        try:
            for task in self._output_service.list():
                if self._stop:
                    logger.info("stop flag is true, restore thread will exit")
                    break

                # step 0, flow control for restore check queue
                while True:
                    if self._stop:
                        break
                    if self._restore_check_queue.qsize() > self._max_restore_check_queue_size:
                        logger.info("restore check queue len: %d, larger than max size: %d, sleep 3 second...",
                                    self._restore_check_queue.qsize(), self._max_restore_check_queue_size)
                        time.sleep(self._sleep_seconds)
                        continue
                    else:
                        break

                # print type(task)
                object_name_ = task.key
                if isinstance(object_name_, unicode):
                    object_name_ = object_name_.encode('utf-8')

                # step 1, check filter to see if real task done or not
                # todo, or use inputservice to check, [name, size, etag]
                # if self._filter.query(object_name_):
                if self._input_service.exists(task):
                    # object had been migrated
                    logger.info("{} has been migrated, skip it".format(object_name_))
                    continue

                # step 2, check filter to see if restored or not
                restore_key = self._restore_prefix + object_name_
                if self._filter.query(restore_key):
                    # object had been restored
                    logger.info("{} has been restored, add it to restore check queue directly".format(object_name_))
                else:
                    # todo, not restored, submit it first time !
                    ret = self._output_service.restore(task.key)
                    # todo, should ret == 202
                    if ret == 400:
                        logger.info("submit task: %s, ret 400, is not archive, operation not supported, skip it", object_name_)
                        continue
                    elif ret == 404:
                        logger.info("submit task: %s, ret 404, not exists, skip it", object_name_)
                        continue
                    elif ret == 202:
                        # todo, submit success !
                        logger.info("submit task: %s, ret 202, restore req has been submitted, waiting for restore ",
                            object_name_)
                    elif ret == 200:
                        # todo, submit success !
                        logger.info("submit task: %s, ret 200, already restore ",
                            object_name_)
                    else:
                        logger.error("submit task: %s, unknown ret code: %d, skip it", object_name_, ret)
                        continue
                # step 3, add to restore check queue
                self._restore_check_queue.put(task)
                logger.info("add task: %s, to restore check queue done, queue size: %d",
                            object_name_, self._restore_check_queue.qsize())
            else:
                logger.info("all task has been submitted or stop flag is true, restore thread will exit")
                self._finish = True
        except Exception as e:
            self._finish = True
            logger.exception(str(e))
        pass

    def check_thread(self):
        assert self._output_service is not None
        try:
            while True:
                if self._stop:
                    logger.info("stop flag is true, check thread will exit")
                    break
                if self.is_finish_normal():
                    logger.info("finish normal: restore thread is finish and check queue is empty, "
                                "so check thread will exit too")
                    break

                try:
                    # logger.debug("try to get task")
                    task = self._restore_check_queue.get_nowait()
                    # logger.debug("get task successfully")
                    self._restore_check_queue.task_done()
                except Empty:
                    logger.debug("restore check queue is empty, will sleep 3 second")
                    time.sleep(self._sleep_seconds)
                    continue

                object_name_ = task.key
                if isinstance(object_name_, unicode):
                    object_name_ = object_name_.encode('utf-8')

                logger.info("get task: %s, from restore check queue done, queue size: %d",
                            object_name_, self._restore_check_queue.qsize())

                # step 1, check restore success or not
                ret = self._output_service.restore(task.key)
                # todo, should ret == 200, is success
                if ret == 409:
                    logger.info("check task: %s, ret 409, object restore is in progress, not finish, put it to restore "
                                "check queue again", object_name_)
                    # todo, put task back to queue again
                    self._restore_check_queue.put(task)
                    continue
                elif ret == 400:
                    logger.info("check task: %s, ret 400, object is not archive, operation not supported, skip it",
                                object_name_)
                    continue
                elif ret == 404:
                    logger.info("check task: %s, ret 404, object not exists, skip it", object_name_)
                    continue
                elif ret == 200:
                    # todo, restore finish !
                    logger.info("check task: %s, ret 200, restore finished, will put it to running task queue",
                                object_name_)
                else:
                    logger.error("unknown ret code: %d, skip it", ret)
                    continue

                # step 2, add restore flag to level db filter
                restore_key = self._restore_prefix + object_name_
                self._filter.add(restore_key)

                # step 3, add task to real task queue
                # flow control for running task queue
                while True:
                    if self._stop:
                        break

                    if self._task_queue.qsize() > self._max_task_queue_size:
                        logger.info("running task queue len: %d, larger than max size: %d, sleep 3 second...",
                                    self._task_queue.qsize(), self._max_task_queue_size)
                        time.sleep(self._sleep_seconds)
                        continue
                    else:
                        self._task_queue.put(task)
                        logger.info("add task: %s, to running task queue done, running task queue size: %d",
                                    task.key, self._task_queue.qsize())
                        break
                    # self._worker.add_task(task)
                    # logger.info("add task: %s, to running task queue done", task.key)
                    break
                pass
        except Exception as e:
            logger.exception(str(e))
        pass

    def start(self):
        # create restore thread
        restore_thread = Thread(target=self.restore_thread, name='restore_thread')
        restore_thread.daemon = True
        self._threads.append(restore_thread)

        # create check thread
        check_thread = Thread(target=self.check_thread, name='check_thread')
        check_thread.daemon = True
        self._threads.append(check_thread)

        for t in self._threads:
            t.start()

    def is_finish_normal(self):
        if self._finish and self._restore_check_queue.empty():
            return True
        return False

    def stop(self, force=False):
        self._stop = True
        for t in self._threads:
            t.join()

if __name__ == '__main__':
    from migrate_tool.services.LocalFileSystem import LocalFileSystem

    migrator = ThreadMigrator(input_service=LocalFileSystem(workspace='F:\\Workspace\\tmp'),
                              output_service=LocalFileSystem(workspace='F:\\logstash-conf'))
    migrator.start()

    import time
    time.sleep(10)
    migrator.stop()
