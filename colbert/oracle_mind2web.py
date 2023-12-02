import openai
import re


def automatic_annotation(df, annotation_constraint = False):

    prompt_example = open('prompt_short.txt', 'r').read() #"prompt.txt"

    constraint = "Provide the predicted action in ``` ```:\n"
    
    max_tokens = 4097 - len(prompt_example) #- len(d)

    # make sure that the returned data is fully annotated
    

    annotations = []
    for data in df.iterrows():
        prompt = f"{prompt_example}\n\\n{data}\n{constraint}" if annotation_constraint else f"{prompt_example}\n\\n{data}"
        response = openai.Completion.create(
            engine= "gpt-3.5-turbo-instruct",
            prompt= prompt,
            max_tokens= max_tokens
        )
        annotated = response.choices[0].text.strip() if response.choices else None
        annotated = re.findall(r'```(.*?)```', annotated, re.DOTALL) if '```' in annotated and annotation_constraint else annotated
        annotations.append(annotated)
    return annotations


def query_gpt_and_check(df, gpt_model):
    responses = []
    is_correct = []

    for index, row in df.iterrows():
        # Construct the prompt from DataFrame elements
        prompt = f"{row['some_column']} {row['another_column']}"  # Modify as per your DataFrame structure

        # Query GPT
        response = openai.Completion.create(
            engine=gpt_model,
            prompt=prompt,
            max_tokens=50  # Adjust as needed
        )

        # Extract response text
        gpt_response = response.choices[0].text.strip()

        # Check if the response is within backticks and matches 'action'
        if gpt_response.startswith('`') and gpt_response.endswith('`'):
            gpt_response = gpt_response[1:-1]  # Remove the backticks
            responses.append(gpt_response)
            is_correct.append(gpt_response == row['action'])
        else:
            responses.append(None)
            is_correct.append(False)

    # Add the responses and correctness check to the DataFrame
    df['gpt_response'] = responses
    df['is_correct'] = is_correct

    return df


if __name__=='__main__':
    updated_df = query_gpt_and_check(df, 'gpt-3.5-turbo')