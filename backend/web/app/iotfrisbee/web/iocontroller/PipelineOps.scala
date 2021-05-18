package iotfrisbee.web.iocontroller

import cats.data.EitherT
import cats.effect.IO
import play.api.mvc.Results.NotFound
import play.api.mvc.{Codec, Result}
import cats.implicits._
import io.circe.Json
import iotfrisbee.protocol.messages.WebResult._
import scala.concurrent.Future
import scala.language.implicitConversions
import iotfrisbee.web.iocontroller.PipelineTypes.PipelineStage
import play.api.http.{ContentTypeOf, Writeable}
import play.api.http.ContentTypes.JSON
import play.api.mvc.Results.Status

object PipelineOps {
  implicit class RichFunctorOption[A](r: IO[Option[A]]) {
    implicit def orRes(res: Result): PipelineStage[IO, A] =
      EitherT {
        r.map(o => Either.fromOption(o, res))
      }

    implicit def orNotFound: PipelineStage[IO, A] = orRes(NotFound("Not Found"))
  }

  implicit class RichFunctor[A](r: IO[A]) {
    implicit def piped: PipelineStage[IO, A] =
      EitherT {
        r.map(a => Either.right[Result, A](a))
      }
  }

  implicit class RichFutureAction[A](f: Future[A]) {
    implicit def asIO: IO[A] = IO.fromFuture(IO(f))
  }

  implicit val contentTypeOfCirceJson: ContentTypeOf[Json] =
    ContentTypeOf[io.circe.Json](Some(JSON))

  implicit def writeableOfCirceJson(implicit codec: Codec): Writeable[Json] = {
    Writeable(obj => codec.encode(obj.noSpaces))
  }

  implicit class RichWebResultWeb(webResult: WebResult) {
    def withHttpStatus(statusCode: Int): Result = Status(statusCode)(webResult.toJsonString).as(JSON)
  }
}
