from .sub_parser_args import SubParserArgs


class SubParserBase:
    def __init__(self, parser_args: SubParserArgs):
        self._parser_args = parser_args
        self._add_common_arguments()

    def _add_common_arguments(self):
        # this method is for future common arguments across sub-parsers
        pass

        # self._parser_args.sub_parser.add_argument("script", help="Path to the entry point script")

        # self._parser_args.sub_parser.add_argument(
        #     "-a",
        #     "--add-python-module",
        #     action="append",
        #     default=[],
        #     help="Add python modules to the output",
        # )

    # @abstractmethod
    # def _add_sub_parser(self) -> None: ...
