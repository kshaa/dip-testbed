package iotfrisbee.web.iocontroller

import cats.data.EitherT
import cats.effect.IO
import play.api.mvc.Results.NotFound
import play.api.mvc.Result
import cats.implicits._
import scala.concurrent.Future
import scala.language.implicitConversions
import iotfrisbee.web.iocontroller.PipelineTypes.PipelineStage

object PipelineOps {
  implicit class FunctorOptionExts[A](r: IO[Option[A]]) {
    implicit def orRes(res: Result): PipelineStage[IO, A] =
      EitherT {
        r.map(o => Either.fromOption(o, res))
      }

    implicit def orNotFound: PipelineStage[IO, A] = orRes(NotFound("Not Found"))
  }

  implicit class FunctorExts[A](r: IO[A]) {
    implicit def piped: PipelineStage[IO, A] =
      EitherT {
        r.map(a => Either.right[Result, A](a))
      }
  }

  implicit class FutureActionExts[A](f: Future[A]) {
    implicit def asIO: IO[A] = IO.fromFuture(IO(f))
  }
}
